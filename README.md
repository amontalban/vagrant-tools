# vagrant-tools
A collection of Python scripts to manage Vagrant boxes in a private repository

## DOCUMENTATION

### Private repository configuration

The private repository can be configured with a [NGINX](1) server, ssh and a
unprivileged user. Basically the server is configured to serve the metadata.json
 file located in the box folder so Vagrant can get box information like versions
 and URLs for them.

As shown below the boxes are stored in /usr/share/nginx/html/vagrant with the
following details:

  - __Box path:__ /usr/share/nginx/html/vagrant/boxname
  - __Metadata path:__ /usr/share/nginx/html/vagrant/boxname/metadata.json
  - __Boxes files:__ /usr/share/nginx/html/vagrant/boxname/boxes/*

__Example of metadata.json__

```json
{
  "description": "This is a example.",
  "name": "amontalban/superbox",
  "versions": [
    {
      "providers": [
        {
          "checksum": "bf74bdbabada3751a91399ab3069d02ed7fa5d0b",
          "checksum_type": "sha1",
          "name": "virtualbox",
          "url": "http://devops.domain.com/vagrant/amontalban/superbox-1.0/boxes/superbox-1.0.box"
        }
      ],
      "version": "1.0"
    }
  ]
}
```

__NGINX server configuration template__
```
server {
    listen 80 default_server;
    listen [::]:80 default_server ipv6only=on;

    root /usr/share/nginx/html;
    index metadata.json;

    server_name devops.domain.com;

    # Match the box name in location and search for its catalog
    # e.g. http://www.example.com/vagrant/devops/ resolves to
    # /var/www/vagrant/devops/devops.json
    #
    location ~ ^/vagrant/([^\/]+)/$ {
        index metadata.json;
        try_files $uri $uri/ metadata.json =404;
        autoindex off;
    }

    location ~ ^/vagrant/([^\/]+)/boxes/$ {
        try_files $uri $uri/ =404;
        autoindex off;
    }

    # Serve json files with content type header application/json
    location ~ \.json$ {
        add_header Content-Type application/json;
    }

    # Serve box files with content type application/octet-stream
    location ~ \.box$ {
        add_header Content-Type application/octet-stream;
    }

    # Deny access to document root and the vagrant folder
    location ~ ^/(vagrant/)?$ {
        return 403;
    }

}
```

The other thing you will need is a user with SSH access to the server and write
rights in the configured path (/usr/share/nginx/html in this case). It's
recommended to use public keys for SSH so you don't have to use passwords. For
more info check this [guide](4).
### vagrant-upload

For more information about this script please check the [documentation](2).

### vagrant-download

For more information about this script please check the [documentation](3).

---

## CHANGELOG

Check the [CHANGELOG](5) to know about recent changes.

## RELATED LINKS

[Vagrant box format](6)
[vube/vagrant-boxer](7)
[Custom Vagrant Cloud Versioned Box Host](8)


[1]: http://nginx.org
[2]: https://github.com/amontalban/vagrant-tools/blob/master/VAGRANT-UPLOAD.md
[3]: https://github.com/amontalban/vagrant-tools/blob/master/VAGRANT-DOWNLOAD.md
[4]: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2
[5]: https://github.com/amontalban/vagrant-tools/blob/master/CHANGELOG.md
[6]: http://docs.vagrantup.com/v2/boxes/format.html
[7]: https://github.com/vube/vagrant-boxer
[8]: http://blog.el-chavez.me/2015/01/31/custom-vagrant-cloud-host/
