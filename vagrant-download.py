#!/usr/bin/env python

import os, sys, argparse, time, tempfile, re, json, shutil, urlparse
import hashlib, tarfile
from urllib2 import Request, urlopen, URLError, HTTPError
from validators import url

#----------------------------------------------------------------------
#-- Script settings

# Default settings
default_provider = "virtualbox"
vm_providers = ['vmware_workstation', 'vmware_fusion', 'virtualbox',
                'docker', 'hyperv']
keep = True

def is_json(json_string):
  try:
    json_object = json.loads(json_string)
  except ValueError, e:
    return False
  return True

def decompress_box(box, outputdir=None):

    tar = tarfile.open(box)
    tar.extractall(outputdir)
    tar.close()

def sha1_file(filename):
   #This function returns the SHA-1 hash of (filename)

   checksum = hashlib.sha1()

   with open(filename,'rb') as file:

       chunk = 0
       while chunk != b'':
           chunk = file.read(1024)
           checksum.update(chunk)

   return checksum.hexdigest()

def md5_file(filename):
   #This function returns the MD5 hash of (filename)

   checksum = hashlib.md5()

   with open(filename,'rb') as file:

       chunk = 0
       while chunk != b'':
           chunk = file.read(1024)
           checksum.update(chunk)

   return checksum.hexdigest()

def get_metadata(url):

    try:
        response = urlopen(url)
    except HTTPError as e:
        if e.code == 404:
            print "METADATA NOT FOUND"
            sys.exit(1)
        else:
            print "--->>>> Couldn't connect to server to get current metadata. <<<<---"
            print "Server failed to fulfill request. Error code: %s" % e.code
            sys.exit(1)
    except URLError as e:
        print "--->>>> Couldn't connect to server to get current metadata. <<<<---"
        print "Failed to connect to server. Reason: %s" % e.reason
        sys.exit(1)
    else:
        output = response.read().decode("utf-8")
        if is_json(output):
            metadata = json.loads(output)
        else:
            print "--->>>> URL isn't a valid JSON file, please check URL. <<<<---"
            sys.exit(1)

    return metadata

def get_latestbox(metadata, selected_provider):

    version = "0.0.0"
    i = 0
    for entry in metadata['versions']:
        if version < entry['version']:
            version = entry['version']
            version_id = i
        i = i + 1

    for provider in metadata['versions'][version_id]["providers"]:
        if selected_provider == provider['name']:
            box = provider

    return box

def get_box(url, output_dir=None):

    if output_dir is None:
        output_dir = os.getcwd()

    output_file = os.path.basename(urlparse.urlsplit(url).path)

    try:
        response = urlopen(url)
    except HTTPError as e:
        if e.code == 404:
            print "BOX FILE NOT FOUND!"
            sys.exit(1)
        else:
            print "--->>>> Couldn't connect to server to get box file. <<<<---"
            print "Server failed to fulfill request. Error code: %s" % e.code
            sys.exit(1)
    except URLError as e:
        print "--->>>> Couldn't connect to server to get box file. <<<<---"
        print "Failed to connect to server. Reason: %s" % e.reason
        sys.exit(1)
    else:
        with open(output_dir + '/' + output_file, 'wb') as file:
            block_size = 8192
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break

                file.write(buffer)

            file.close()

    fullpath = output_dir + '/' + output_file

    return fullpath

#-------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="This script downloads latest version of a vagrant box.")
parser.add_argument("--url", "-u", required=True, metavar="url", help="URL of the box you want to download.")
parser.add_argument("--provider", "-p", metavar="provider", help="Default provider for the box you want to download (i.e vmware) (Default is virtualbox).")
parser.add_argument("--outputdir", "-o", metavar="outputdir", help="Path to the output folder where you want to store the download box (Default is current directory).")
parser.add_argument("-d", action='store_true', help="Use this flag if you want to decompress the downloaded box (Default no).")
parser.add_argument("-k", action='store_true', help="Use this flag if you want to keep the downloaded box in case you use the --decompress option (Default no).")

args = parser.parse_args()

if len(sys.argv) > 1:
    if url(args.url):
        metadata = get_metadata(args.url)
        if args.provider is not None:
            for provider in vm_providers:
                if provider == args.provider.lower():
                    selected_provider = args.provider.lower()
                    box = get_latestbox(metadata, selected_provider)

                    if args.outputdir is not None:
                        if os.path.isdir(args.outputdir):
                            boxfile = get_box(box['url'], args.outputdir)
                            if box['checksum_type'] == 'sha1':
                                checksum = sha1_file(boxfile)
                            elif box['checksum_type'] == 'md5':
                                checksum = md5_file(boxfile)
                            else:
                                print "Checksum not supported"
                                sys.exit(1)

                            if checksum == box['checksum']:
                                print "Box downloaded and validated"
                                if args.d is not None:
                                    if args.d:
                                        decompress_box(boxfile, args.outputdir)
                                        if args.k is not None:
                                            if args.k:
                                                print "Downloaded box has been kept"
                                            else:
                                                os.remove(boxfile)
                            else:
                                print "Box file checksum not valid"
                                sys.exit(1)
                        else:
                            print "Outputdir isn't a valid path"
                            sys.exit(1)
                    else:
                        boxfile = get_box(box['url'])
                        if box['checksum_type'] == 'sha1':
                            checksum = sha1_file(boxfile)
                        elif box['checksum_type'] == 'md5':
                            checksum = md5_file(boxfile)
                        else:
                            print "Checksum not supported"
                            sys.exit(1)

                        if checksum == box['checksum']:
                            print "Box downloaded and validated"
                            if args.d is not None:
                                if args.d:
                                    decompress_box(boxfile)
                                    if args.k is not None:
                                        if args.k:
                                            print "Downloaded box has been kept"
                                        else:
                                            os.remove(boxfile)
                        else:
                            print "Box file checksum not valid"
                            sys.exit(1)

        else:
            selected_provider = default_provider
            box = get_latestbox(metadata, selected_provider)

            boxfile = get_box(box['url'])
            if box['checksum_type'] == 'sha1':
                checksum = sha1_file(boxfile)
            elif box['checksum_type'] == 'md5':
                checksum = md5_file(boxfile)
            else:
                print "Checksum not supported"
                sys.exit(1)

            if checksum == box['checksum']:
                if args.d is not None:
                    if args.d:
                        decompress_box(boxfile, args.outputdir)
                        if args.k is not None:
                            if args.k:
                                print "Downloaded box has been kept"
                            else:
                                os.remove(boxfile)
    else:
        print "Entered URL is not valid, please check and try again"
        sys.exit(1)
