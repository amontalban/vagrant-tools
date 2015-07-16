# vagrant-download

This script is intended to be used when you want to download a Vagrant box from
 the repository. It's useful when for example you want to build a Packer image
from a base box using [vagrant-ovf][1] builder.
__Usage__

```
usage: vagrant-download.py [-h] --url url [--provider provider]
                           [--outputdir outputdir] [-d] [-k]

This script downloads latest version of a vagrant box.

optional arguments:
  -h, --help            show this help message and exit
  --url url, -u url     URL of the box you want to download.
  --provider provider, -p provider
                        Default provider for the box you want to download (i.e
                        vmware) (Default is virtualbox).
  --outputdir outputdir, -o outputdir
                        Path to the output folder where you want to store the
                        download box (Default is current directory).
  -d                    Use this flag if you want to decompress the downloaded
                        box (Default no).
  -k                    Use this flag if you want to keep the downloaded box
                        in case you use the --decompress option (Default no).
```
[1]: https://packer.io/docs/builders/virtualbox-ovf.html
