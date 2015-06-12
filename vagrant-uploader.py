#!/usr/bin/env python

import os, sys, argparse, time, tempfile, re, json, shutil
from urllib2 import Request, urlopen, URLError, HTTPError
import hashlib
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

def display_error(message):
    print colors.FAIL + colors.BOLD + colors.UNDERLINE + message + colors.ENDC


def display_ok(message):
    print colors.OKGREEN + message + colors.ENDC


def boxname_parser(name):
    result = {}
    boxname_regex = "(?P<company>(?:^[a-zA-Z0-9\-\_\.]*))\/(?P<name>(?:[a-zA-Z0-9\-\_\.]*))"

    regex = re.compile(boxname_regex)
    if regex.match(name) is not None:
        regex = re.match(boxname_regex, name)
        result["company"] = regex.group('company')
        result["name"] = regex.group('name')

    return result


def load_settings(settings="metadata.json"):
    if os.path.isfile(settings):
        with open(settings) as defaults_file:
            defaults = json.load(defaults_file)

        return defaults


def sha1_file(filename):
   #This function returns the SHA-1 hash of (filename)

   checksum = hashlib.sha1()

   with open(filename,'rb') as file:

       chunk = 0
       while chunk != b'':
           chunk = file.read(1024)
           checksum.update(chunk)

   return checksum.hexdigest()


def validate_settings(config):

    if config.get("provider") is None:
        display_error("Provider not defined in metadata file, this is a required field.")
        display_error("--->>>> Please set provider value in metadata file <<<<---")
        sys.exit(1)

    if config.get("file") is None:
        display_error("File not defined in metadata file, this is a required field.")
        display_error("--->>>> Please set file value in metadata file <<<<---")
        sys.exit(1)
    else:
        if os.path.isfile(config.get("file")):
            if not config.get("file").lower().endswith('.box'):
                display_error("Box filename needs to ends with .box")
                display_error("--->>>> Please change box filename in metadata file <<<<---")
                sys.exit(1)
        else:
                display_error("Box filename path is not a file!")
                display_error("--->>>> Please change box filename path in metadata file <<<<---")
                sys.exit(1)

    if config.get("baseurl") is None:
        display_error("Base URL not defined in metadata file, this is a required field.")
        display_error("--->>>> Please set baseurl value in metadata file <<<<---")
        sys.exit(1)

    if config.get("remotepath") is None:
        display_error("Remote path not defined in metadata file, this is a required field.")
        display_error("--->>>> Please set remote path value in metadata file <<<<---")
        sys.exit(1)

    if config.get("server") is None:
        display_error("Server not defined in metadata file, this is a required field.")
        display_error("--->>>> Please set server value in metadata file <<<<---")
        sys.exit(1)

    if config.get("description") is None:
        config["description"] = "No description provided."

    if config.get("name") is not None:
        parsedname = boxname_parser(config.get("name"))
        config["company"] = parsedname.get("company")
        config["name"] = parsedname.get("name")
    else:
        config["company"] = "undefined"
        config["name"] = "undefined"

    return config

def generate_metadata(box, metadata=None):

    if metadata is not None:
        version = {}
        version["version"] = box["version"]

        entry = {}
        entry["name"] = box["provider"]
        entry["url"] = box["baseurl"] + "/" + box["company"] + "/" + box["name"] + "/boxes/" + os.path.basename(box["file"])
        entry["checksum_type"] = "sha1"
        entry["checksum"] = sha1_file(box["file"])

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
        entry["url"] = box["baseurl"] + "/" + box["company"] + "/" + box["name"] + "/boxes/" + os.path.basename(box["file"])
        entry["checksum_type"] = "sha1"
        entry["checksum"] = sha1_file(box["file"])

        providers = version
        providers["providers"] = [entry]

        metadata["versions"] = [providers]

    return metadata

#-------------------------------------------------------------------------------

#-- Core script
parser = argparse.ArgumentParser(description="This script uploads the .box file to server on specified path and update metadata file.")
parser.add_argument("--config", "-c", metavar="config", help="Full path to defaults settings config file (In json format, check config.json)")
parser.add_argument("--name", "-n", metavar="name", help="The name of the box in the following syntax company/boxname")
parser.add_argument("--file", "-f", metavar="file", help="The path to the .box file i.e /home/user/mybox.box")
parser.add_argument("--provider", "-p", metavar="provider", help="The name of the provider for the box.")
parser.add_argument("--description", "-d", metavar="description", help="The description of the box.")
parser.add_argument("--version", "-v", metavar="version", help="The version number of the box.")
parser.add_argument("--baseurl", "-b", metavar="baseurl", help="The base URL where box is going to be served.")
parser.add_argument("--serverpath", "-s", metavar="serverpath", help="Full path to server in the following format username@fqdn.domain.com:/path/to/webroot")

args = parser.parse_args()

# We check if --configfile is configured and use that instead of default name
if args.config is not None:
    if os.path.isfile(args.config):
        default_settings = args.config
    else:
        display_error("Configuration file is not a file, please check config file path")
        sys.exit(1)

# We use default settings file if present
if os.path.isfile(default_settings):
    if load_settings(default_settings) is not None:
        # Load settings
        display_ok("Loading settings...")
        config = load_settings(default_settings)

        box = validate_settings(config)

        # We create a temp folder where we are going to copy box and metadata
        # before uploading it to server
        if os.path.isfile(box.get("file")):
            display_ok("Creating temp directory...")
            # Create a randomic temporary folder
            tempfolder = tempfile.mkdtemp()
            directory = os.path.realpath(os.path.join(tempfolder, box.get("company"), box.get("name")))
            os.makedirs(directory)

            display_ok("Copying box file...")
            # Copy box to temp folder
            boxes = os.path.realpath(os.path.join(directory, "boxes"))
            os.makedirs(boxes)
            shutil.copy(box.get("file"), boxes)

            display_ok("Checking current metadata...")
            metadata_url = box.get("baseurl") + "/" + box.get("company") + "/" + box.get("name")
            remote_metadata = Request(metadata_url)
            try:
                response = urlopen(remote_metadata)
            except HTTPError as e:
                if e.code == 404:
                    display_ok("No current metadata found, creating it...")
                    # This is first upload of box
                    metadata = generate_metadata(box)

                    with open(directory + '/metadata.json', 'w') as output_file:
                        json.dump(metadata, output_file, sort_keys=True, indent=2, separators=(',', ': '))

                    display_ok("Uploading box and metadata to repository...")
                    with hide('output','running','warnings'), settings(warn_only=True, host_string=box["server"]):
                        result = put(tempfolder + "/" + box.get("company"), box.get("remotepath"))

                        if result.failed:
                            display_error("--->>>> UPLOADING BOX FAILED! <<<<---")
                            display_error("Check Internet connection or access to remote server")
                            sys.exit(1)
                        else:
                            display_ok("Box " + box.get("company") + "/" + box.get("name") + " uploaded successfully!")

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
                display_ok("Updating box " + box.get("company") + "/" + box.get("name") + "...")
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

                    display_ok("Uploading box and metadata to repository...")
                    with hide('output','running','warnings'), settings(warn_only=True, host_string=box["server"]):
                        result = put(tempfolder + "/" + box.get("company"), box.get("remotepath"))

                        if result.failed:
                            display_error("--->>>> UPLOADING BOX FAILED! <<<<---")
                            display_error("Check Internet connection or access to remote server")
                            sys.exit(1)
                        else:
                            display_ok("Box " + box.get("company") + "/" + box.get("name") + " uploaded successfully!")

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
