#!/usr/bin/env python

import os, sys, argparse, time, tempfile, re, json, shutil
from urllib2 import Request, urlopen, URLError, HTTPError
from hashlib import sha1
from collections import OrderedDict
from pprint import pprint
from fabric.api import run, env, put, hosts, sudo, settings, hide, get, local
from fabric.tasks import execute

#-------------------------------------------------------------------------------
#-- Script settings

env.use_ssh_config = True
default_settings = "config.json"

#-------------------------------------------------------------------------------

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def display_error(error):
    print colors.FAIL + error + colors.ENDC


def box_name_parser(name):
    result = {}
    boxname_regex = "(?P<company>(?:^[a-zA-Z0-9\-\_\.]*))\/(?P<name>(?:[a-zA-Z0-9\-\_\.]*))"

    regex = re.compile(boxname_regex)
    if regex.match(name) is not None:
        regex = re.match(boxname_regex, name)
        result["company"] = regex.group('company')
        result["name"] = regex.group('name')

    return result


def read_defaults(settings="metadata.json"):
    if os.path.isfile(settings):
        with open(settings) as defaults_file:
            defaults = json.load(defaults_file)
            provider = defaults.get("provider")
            file = defaults.get("file")
            baseurl = defaults.get("baseurl")
            if provider is None:
                display_error("Provider not defined in metadata file, this is a required field.")
                display_error("--->>>> Please set provider value in metadata file <<<<---")
                sys.exit(1)
            if file is None:
                display_error("File not defined in metadata file, this is a required field.")
                display_error("--->>>> Please set file value in metadata file <<<<---")
                sys.exit(1)
            if baseurl is None:
                display_error("Base URL not defined in metadata file, this is a required field.")
                display_error("--->>>> Please set baseurl value in metadata file <<<<---")
                sys.exit(1)

            if not file.lower().endswith('.box'):
                display_error("Box filename needs to ends with .box")
                display_error("--->>>> Please change box filename in metadata file <<<<---")
                sys.exit(1)

            return defaults


def generate_metadata(box, metadata=None):

    if metadata is not None:
        version = {}
        version["version"] = box["version"]

        entry = {}
        entry["name"] = box["provider"]
        entry["url"] = box["baseurl"] + "/" + box["company"] + "/" + box["name"] + "/boxes/" + box["file"]
        entry["checksum_type"] = "sha1"
        entry["checksum"] = sha1(box["file"]).hexdigest()

        providers = version
        providers["providers"] = [entry]

        metadata["versions"] = metadata["versions"] + [providers]

    else:
        metadata = {}
        metadata["name"] = box["company"] + "/" + box["name"]
        metadata["description"] = box["description"]

        version = {}
        version["version"] = box["version"]

        entry = {}
        entry["name"] = box["provider"]
        entry["url"] = box["baseurl"] + "/" + box["company"] + "/" + box["name"] + "/boxes/" + box["file"]
        entry["checksum_type"] = "sha1"
        entry["checksum"] = sha1(box["file"]).hexdigest()

        providers = version
        providers["providers"] = [entry]

        metadata["versions"] = [providers]

    return metadata

#-------------------------------------------------------------------------------

#-- Core script
parser = argparse.ArgumentParser(description="This script uploads the .box file to server on specified path and update metadata file.")
parser.add_argument("--name", metavar="name", help="The name of the box in the following syntax company/boxname")
parser.add_argument("--file", metavar="file", help="The path to the .box file i.e /home/user/mybox.box")
parser.add_argument("--provider", metavar="provider", help="The name of the provider for the box.")
parser.add_argument("--description", metavar="description", help="The description of the box.")
parser.add_argument("--version", metavar="version", help="The version number of the box.")
parser.add_argument("--baseurl", metavar="baseurl", help="The base URL where box is going to be served.")
parser.add_argument("--serverpath", metavar="serverpath", help="Full path to server in the following format username@fqdn.domain.com:/path/to/webroot")

# We use default settings file if present
if os.path.isfile(default_settings):
    if read_defaults(default_settings) is not None:
        box = read_defaults(default_settings)

        # Parse boxname in format company/boxname and add it to box dict
        if box.get("name") is not None:
            parsedname = box_name_parser(box.get("name"))
            box["company"] = parsedname.get("company")
            box["name"] = parsedname.get("name")
        else:
            box["company"] = "undefined"
            box["name"] = "undefined"

        # We create a temp folder where we are going to copy box and metadata
        # before uploading it to server
        if os.path.isfile(box.get("file")):
            # Create a randomic temporary folder
            tempfolder = tempfile.mkdtemp()
            directory = os.path.realpath(os.path.join(tempfolder, box.get("company"), box.get("name")))
            os.makedirs(directory)

            # Copy box to temp folder
            boxes = os.path.realpath(os.path.join(directory, "boxes"))
            os.makedirs(boxes)
            shutil.copy(box.get("file"), boxes)

            metadata_url = box.get("baseurl") + "/" + box.get("company") + "/" + box.get("name")
            remote_metadata = Request(metadata_url)
            try:
                response = urlopen(remote_metadata)
            except HTTPError as e:
                if e.code == 404:
                    # This is first upload of box
                    metadata = generate_metadata(box)

                    with open(directory + '/metadata.json', 'w') as output_file:
                        json.dump(metadata, output_file, sort_keys=True, indent=2, separators=(',', ': '))

                    with hide('output','running','warnings'), settings(warn_only=True, host_string=box["server"]):
                        result = put(tempfolder + "/" + box.get("company"), box.get("remotepath"))

                        if result.failed:
                            display_error("--->>>> UPLOADING BOX FAILED! <<<<---")
                            display_error("Check Internet connection or access to remote server")
                            sys.exit(1)

                    # Delete tempfolder
                    shutil.rmtree(tempfolder)
                else:
                    display_error("--->>>> Couldn't connect to server to get current metadata. <<<<---")
                    display_error("Server failed to fulfill request. Error code: %s" % e.code)
                    sys.exit(1)
            except URLError as e:
                display_error("--->>>> Couldn't connect to server to get current metadata. <<<<---")
                display_error("Failed to connect to server. Reason: %s" % e.reason)
                sys.exit(1)
            else:
                # Box was uploaded before, we need to update metadata
                # and upload new version if it's not there
                current_metadata = json.load(response)

                # We check if the box version isn't already uploaded/defined
                # in server metadata.json
                already_uploaded = False
                for entry in current_metadata['versions']:
                    if box["version"] == entry['version']:
                        already_uploaded = True

                if not already_uploaded:
                    metadata = generate_metadata(box, current_metadata)

                    with open(directory + '/metadata.json', 'w') as output_file:
                        json.dump(metadata, output_file, sort_keys=True, indent=2, separators=(',', ': '))

                    with hide('output','running','warnings'), settings(warn_only=True, host_string=box["server"]):
                        result = put(tempfolder + "/" + box.get("company"), box.get("remotepath"))

                        if result.failed:
                            display_error("--->>>> UPLOADING BOX FAILED! <<<<---")
                            display_error("Check Internet connection or access to remote server")
                            sys.exit(1)
                else:
                    display_error("--->>>> THIS BOX VERSION WAS ALREADY UPLOADED! <<<<---")
                    display_error("Please check box version")
                    sys.exit(1)

                # Delete tempfolder
                shutil.rmtree(tempfolder)
        else:
            display_error("File path defined in metadata file is not a file.")
            display_error("--->>>> Please correct file value in metadata file <<<<---")
            sys.exit(1)
# If no default settings file is present, use args
else:
    if len(sys.argv) > 1:
        print "Hello there!"
        # TODO
        # Parse args and do same as before
        #else:
        # No args fail hard!
