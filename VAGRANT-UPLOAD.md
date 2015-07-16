# vagrant-upload

This script is intended to be used when you want to upload a Vagrant box to the
repository. If box metadata exists it will update it and if it doesn't exist it
create it.

The script can read the default settings from a JSON file (By default this file
is called config.json).

All other parameters are customizable via command line.

__Usage__

```
usage: vagrant-uploader.py [-h] [--config config] [--name name] [--file file]
                           [--provider provider] [--description description]
                           [--version version] [--baseurl baseurl]
                           [--serverpath serverpath]

This script uploads the .box file to server on specified path and update
metadata file.

optional arguments:
  -h, --help            show this help message and exit
  --config config, -c config
                        Full path to defaults settings config file (In json
                        format, check config.json)
  --name name, -n name  The name of the box in the following syntax
                        company/boxname
  --file file, -f file  The path to the .box file i.e /home/user/mybox.box
  --provider provider, -p provider
                        The name of the provider for the box.
  --description description, -d description
                        The description of the box.
  --version version, -v version
                        The version number of the box.
  --baseurl baseurl, -b baseurl
                        The base URL where box is going to be served.
  --serverpath serverpath, -s serverpath
                        Full path to server in the following format
                        username@fqdn.domain.com:/path/to/webroot
```

__Configuration file example___

```json
{
  "name": "hashicorp/precise64",
  "file": "precise64_011_virtualbox.box",
  "description": "This box contains Ubuntu 12.04 LTS 64-bit.",
  "provider": "virtualbox",
  "version": "0.0.1",
  "baseurl": "http://your.server.com/vagrant",
  "server": "user@your.server.com",
  "remotepath": "/path/to/your/webroot/vagrant"
}
```
