# CHANGELOG

## 0.0.2

__NEW FEATURES:__

   * Created new script called `vagrant-downloader` to download boxes from\
   repository so for example you can use base boxes for new Packer generated
   boxes.

__IMPROVEMENTS:__

   * Update documentation.
   * Add a requirements.txt file to install Python packages.

---

## 0.0.1

__IMPROVEMENTS:__

  * Validate config values
  * Set a message for every step in the process

__BUG FIXES:__

  * SHA1 wasn't calculated properly
  * Configure metadata to not upload complete box file path, just box file name.
