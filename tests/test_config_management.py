#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of ofunctions module

"""
Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes
"""

__intname__ = "tests.traceroute_history.config_management"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2022 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2022050501"

from traceroute_history import config_management


def test_read_smokeping_config():
    conf_file = "tests/smokeping_example_configs/smokeping_example1.conf"
    targets = config_management.read_smokeping_config(conf_file)
    print(targets)
    assert targets == [{'target': 'localhost', 'name': 'The NOC@intERLab'}, {'target': 'pc1', 'name': 'pc1'}, {'target': 'pc2', 'name': 'pc2'}, {'target': 'pc3', 'name': 'pc3'}, {'target': 'pc4', 'name': 'pc4'}, {'target': 'pc5', 'name': 'pc5'}, {'target': 'pc6', 'name': 'pc6'}, {'target': 'pc7', 'name': 'pc7'}, {'target': 'pc8', 'name': 'pc8'}, {'target': 'pc9', 'name': 'pc9'}, {'target': 'pc10', 'name': 'pc10'}, {'target': 'pc11', 'name': 'pc11'}, {'target': 'pc12', 'name': 'pc12'}, {'target': 'pc13', 'name': 'pc13'}, {'target': 'pc14', 'name': 'pc14'}, {'target': 'pc15', 'name': 'pc15'}, {'target': 'localhost', 'name': 'Apache 2 Server for noc'}, {'target': 'pc1', 'name': 'Apache 2 Server for pc1'}, {'target': 'pc2', 'name': 'Apache 2 Server for pc2'}, {'target': 'pc3', 'name': 'Apache 2 Server for pc3'}, {'target': 'pc4', 'name': 'Apache 2 Server for pc4'}, {'target': 'pc5', 'name': 'Apache 2 Server for pc5'}, {'target': 'pc6', 'name': 'Apache 2 Server for pc6'}, {'target': 'pc7', 'name': 'Apache 2 Server for pc7'}, {'target': 'pc8', 'name': 'Apache 2 Server for pc8'}, {'target': 'pc9', 'name': 'Apache 2 Server for pc9'}, {'target': 'pc10', 'name': 'Apache 2 Server for pc10'}, {'target': 'pc11', 'name': 'Apache 2 Server for pc11'}, {'target': 'pc12', 'name': 'Apache 2 Server for pc12'}, {'target': 'pc13', 'name': 'Apache 2 Server for pc13'}, {'target': 'pc14', 'name': 'Apache 2 Server for pc14'}, {'target': 'pc15', 'name': 'Apache 2 Server for pc15'}, {'target': 'noc', 'name': 'Name Server Latency for noc'}, {'target': 'afnog.org', 'name': 'African Network Operators Group'}, {'target': 'nsrc.org', 'name': 'NSRC (Eugene, Oregon, USA)'}, {'target': 'ws.edu.isoc.org', 'name': 'ISOC Workshop Resource Centre (Eugene, Oregon, USA)'}, {'target': 'shell.uoregon.edu', 'name': 'Main User Box, University of Oregon (Eugene, Oregon, USA)'}, {'target': 'sageduck.org', 'name': 'sageduck.org'}], "Bogus smokeping example 1 test"

    conf_file = "tests/smokeping_example_configs/smokeping_example2.conf"
    targets = config_management.read_smokeping_config(conf_file)
    assert targets == [{'target': 'localhost', 'name': 'The NOC@intERLab'}, {'target': 'pc1', 'name': 'pc1'}, {'target': 'pc2', 'name': 'pc2'}, {'target': 'pc3', 'name': 'pc3'}, {'target': 'pc4', 'name': 'pc4'}, {'target': 'pc5', 'name': 'pc5'}, {'target': 'pc6', 'name': 'pc6'}, {'target': 'pc7', 'name': 'pc7'}, {'target': 'pc8', 'name': 'pc8'}, {'target': 'pc9', 'name': 'pc9'}, {'target': 'pc10', 'name': 'pc10'}, {'target': 'pc11', 'name': 'pc11'}, {'target': 'pc12', 'name': 'pc12'}, {'target': 'pc13', 'name': 'pc13'}, {'target': 'pc14', 'name': 'pc14'}, {'target': 'pc15', 'name': 'pc15'}, {'target': 'includedPC1', 'name': 'Apache 2 Server for includedPC1'}, {'target': 'includedPC2', 'name': 'Apache 2 Server for includedPC1'}, {'target': 'localhost', 'name': 'Apache 2 Server for noc'}, {'target': 'pc1', 'name': 'Apache 2 Server for pc1'}, {'target': 'pc2', 'name': 'Apache 2 Server for pc2'}, {'target': 'pc3', 'name': 'Apache 2 Server for pc3'}, {'target': 'pc4', 'name': 'Apache 2 Server for pc4'}, {'target': 'pc5', 'name': 'Apache 2 Server for pc5'}, {'target': 'pc6', 'name': 'Apache 2 Server for pc6'}, {'target': 'pc7', 'name': 'Apache 2 Server for pc7'}, {'target': 'pc8', 'name': 'Apache 2 Server for pc8'}, {'target': 'pc9', 'name': 'Apache 2 Server for pc9'}, {'target': 'pc10', 'name': 'Apache 2 Server for pc10'}, {'target': 'pc11', 'name': 'Apache 2 Server for pc11'}, {'target': 'pc12', 'name': 'Apache 2 Server for pc12'}, {'target': 'pc13', 'name': 'Apache 2 Server for pc13'}, {'target': 'pc14', 'name': 'Apache 2 Server for pc14'}, {'target': 'pc15', 'name': 'Apache 2 Server for pc15'}, {'target': 'noc', 'name': 'Name Server Latency for noc'}, {'target': 'afnog.org', 'name': 'African Network Operators Group'}, {'target': 'nsrc.org', 'name': 'NSRC (Eugene, Oregon, USA)'}, {'target': 'ws.edu.isoc.org', 'name': 'ISOC Workshop Resource Centre (Eugene, Oregon, USA)'}, {'target': 'shell.uoregon.edu', 'name': 'Main User Box, University of Oregon (Eugene, Oregon, USA)'}, {'target': 'sageduck.org', 'name': 'sageduck.org'}], "Bogus smokeping example 2 test with inclusions"
    print(targets)

    conf_file = "tests/smokeping_example_configs/smokeping_example3.conf"
    targets = config_management.read_smokeping_config(conf_file)
    assert targets == [{'target': 'www.cdn77.com', 'name': 'ANYCAST CDN77 (AS60068 www.cdn77.com)'}, {'target': '1.1.1.1', 'name': 'ANYCAST Cloudflare (AS13335 1.1.1.1)'}, {'target': '192.175.48.1', 'name': 'ANYCAST DNS-OARC (AS112 192.175.48.1)'}, {'target': 'www.googleapis.com', 'name': 'ANYCAST Google API (AS15169 www.googleapis.com)'}, {'target': '8.8.8.8', 'name': 'ANYCAST Google DNS (AS15169 8.8.8.8)'}, {'target': 'drive.google.com', 'name': 'ANYCAST Google DRIVE (AS15169 drive.google.com)'}, {'target': '9.9.9.9', 'name': 'ANYCAST Quad9 (AS19281 9.9.9.9)'}, {'target': 'ns1.wordpress.com', 'name': 'ANYCAST WordPress (AS2635 ns1.wordpress.com)'}, {'target': 'ovh.es', 'name': '[FR] ISP OVH (AS16276 ovh.es)'}, {'target': 'nsa.online.net', 'name': '[FR] ISP Online.net (AS12876 nsa.online.net)'}, {'target': 'hetzner.com', 'name': '[DE] ISP Hetzner (AS24940 hetzner.com)'}], "Bogus smokeping example 3 test with inclusions"
    print(targets)

if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test_read_smokeping_config()
