# Traceroute History

Traceroute history records Unix traceroute & Windows tracert outputs to a database, upon hop changes.
It can be run via cron / task scheduler or as service.

## Setup

1. Adjust the configuration file `traceroute_history.conf` according to your needs.
2. Initialize the database
   `traceroute_history.py --config=traceroute_history.conf --init-db`
3. Run via cron
   `traceroute_history.py --config=traceroute_history.conf --update-now`
   
   or run as service
   `traceroute_history.py --config=traceroute_history.conf --daemon`
   
## User interface

FastCGI smokeping integration is ongoing.
A full blown user interface is also ongoing.
