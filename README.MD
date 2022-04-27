# Traceroute History

Traceroute History is under heavy developpment (see TODO.TXT).

Traceroute History records Unix traceroute & Windows tracert outputs to a database, upon host changes in hops, or big rtt increases to hops.
The core can be run as a service or as a cron task, both providing regular probe updates.
It can be run via cron / task scheduler or as service.

## Setup

1. Install traceroute binary via `dnf install traceroute`. On Windows, binary `tracert` should be included in system32 directory.
1. Install development tools via `dnf install python3-devel gcc make` in order to compile required python modules.
2. Install requirements via `pip -m install -r requirements.txt` and `pip -m install -r requirements-python36.txt` if you run with Python 3.6
3. Adjust the configuration file `traceroute_history.conf` according to your needs.
4. Initialize the database
   `traceroute_history.py --config=traceroute_history.conf --init-db`
5. Run as cron task with `traceroute_history.py --config=traceroute_history.conf --update-now`
   
   Example of a cron entry in /etc/crontab
   
   `30 * * * * root /usr/bin/python3 /opt/traceroute_history/traceroute_history.py --config=/opt/traceroute_history/traceroute_history.conf --update-now`
   
   or run as service
   `traceroute_history.py --config=traceroute_history.conf --daemon`

## User interface

There's currently a CLI and a GUI interface available.
CLI can be executed directly via the script, eg:

`traceroute_history.py --help`

GUI relies on FastAPI and uvicorn modules.

GUI can be launched via `user_interface.py` and will by default listen on 127.0.0.1:5001. Bind ip and port be modified in `traceroute_history.conf`.

Additionnaly, a systemd file is provided for launching the user interface in `extras`

```
cp extras/traceroute_history_ui.service /usr/lib/systemd/system
systemctl enable --now traceroute_history_ui
systemctl status traceroute_history_ui
```

![Test Image 1](current_ui_state.png)
   
## Smokeping integration - Webserver

Traceroute History can directly read smokeping configuration files in order to add them as probe targets.
It also provides a FastCGI script that can be directly integrated into smokeping:

### Apache

In your smokeping virtualhost add

```
<Directory "/path/to/traceroute_history">
    require all granted
</Directory>

Alias /smokeping_th_helper.fcgi /path/to/traceroute_history/smokeping_th_helper.fgci
```

### Nginx

You need to install fcgiwrap for CGI wrapper interact with Nginx:

* Debian/Ubuntu: `apt install fcgiwrap`
* CentOS/RHEL: `yum install fcgiwrap`

Then configure Nginx with the default configuration:

`cp /usr/share/doc/fcgiwrap/examples/nginx.conf /etc/nginx/fcgiwrap.conf`

Make symbolic link for smokeping_th_helper.fcgi:

`ln': ln -s /opt/traceroute_history/smokeping_th_helper.fcgi /usr/lib/cgi-bin/smokeping_th_helper.fcgi`

In your smokeping virtualhost add

```
location = /smokeping/smokeping_th_helper.fcgi {
        alias /opt/traceroute_history/smokeping_th_helper.fcgi;

        fastcgi_intercept_errors on;

        fastcgi_param   SCRIPT_FILENAME         /usr/lib/cgi-bin/smokeping_th_helper.fcgi;
        fastcgi_param   QUERY_STRING            $query_string;
        fastcgi_param   REQUEST_METHOD          $request_method;
        fastcgi_param   CONTENT_TYPE            $content_type;
        fastcgi_param   CONTENT_LENGTH          $content_length;
        fastcgi_param   REQUEST_URI             $request_uri;
        fastcgi_param   DOCUMENT_URI            $document_uri;
        fastcgi_param   DOCUMENT_ROOT           $document_root;
        fastcgi_param   SERVER_PROTOCOL         $server_protocol;
        fastcgi_param   GATEWAY_INTERFACE       CGI/1.1;
        fastcgi_param   SERVER_SOFTWARE         nginx/$nginx_version;
        fastcgi_param   REMOTE_ADDR             $remote_addr;
        fastcgi_param   REMOTE_PORT             $remote_port;
        fastcgi_param   SERVER_ADDR             $server_addr;
        fastcgi_param   SERVER_PORT             $server_port;
        fastcgi_param   SERVER_NAME             $server_name;
        fastcgi_param   HTTPS                   $https if_not_empty;

        fastcgi_pass unix:/var/run/fcgiwrap.socket;
}
```

## Smokeping integration - HTML

In your smokeping basepage.html file (generally in /opt/smokeping/etc), add the `smokeping_th_helper.js` script after the other scripts.
Your source should look like: 
```
<script src="js/prototype.js" type="text/javascript"></script>
<script src="js/scriptaculous/scriptaculous.js?load=builder,effects,dragdrop" type="text/javascript"></script>
<script src="js/cropper/cropper.js" type="text/javascript"></script>
<script src="js/smokeping.js" type="text/javascript"></script>
// Added script
<script src="js/smokeping_th_helper.js" type="text/javascript"></script>
```

Also copy `smokeping_th_helper.js` to your `www/js` folder.

