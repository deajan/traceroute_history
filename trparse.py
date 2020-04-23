# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Luis Benitez
Copyright (C) 2020 Orsiris de Jong

Current version 0.4.0 supports windows tracert and fixes a couple of bugs

Parses the output of a traceroute execution into an AST (Abstract Syntax Tree).
"""

import re

from decimal import Decimal

# Add [ ] for windows compat
RE_HEADER = re.compile(r'(\S+)\s+(?:\(|\[)(?:(\d+\.\d+\.\d+\.\d+)|([0-9a-fA-F:]+))(?:\)|\])')

RE_PROBE_NAME_IP = re.compile(r'(\S+)\s+(?:\(|\[)(?:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|([0-9a-fA-F:]+))(?:\)|\])+')
RE_PROBE_IP_ONLY = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})+')
RE_PROBE_ANNOTATION = re.compile(r'^(!\w*)$')
RE_PROBE_TIMEOUT = re.compile(r'^(\*)$')

RE_HOP_INDEX = re.compile(r'^\s*(\d+)\s+')
RE_FIRST_HOP = re.compile(r'^\s*(\d+)\s+(.+)')
RE_HOP = re.compile(r'^\s*(\d+)?\s+(.+)$')
RE_PROBE_ASN = re.compile(r'\[AS(\d+)\]')
RE_PROBE_RTT_ANNOTATION = re.compile(r'(?:(\d+(?:\.?\d+)?)\s+ms|(\s+\*\s+))\s*(!\S*)?')


class Traceroute(object):
    """
    Abstraction of a traceroute result.
    """
    def __init__(self, dest_name, dest_ip):
        self.dest_name = dest_name
        self.dest_ip = dest_ip
        self.hops = []

    def add_hop(self, hop):
        self.hops.append(hop)

    def __str__(self):
        text = "Traceroute object for %s (%s)\n\n" % (self.dest_name, self.dest_ip)
        for hop in self.hops:
            text += str(hop)
        return text


class Hop(object):
    """
    Abstraction of a hop in a traceroute.
    """
    def __init__(self, idx):
        self.idx = idx  # Hop count, starting at 1
        self.probes = []  # Series of Probe instances

    def add_probe(self, probe):
        """Adds a Probe instance to this hop's results."""
        if self.probes:
            probe_last = self.probes[-1]
            if not probe.ip:
                probe.ip = probe_last.ip
                probe.name = probe_last.name
        self.probes.append(probe)

    def __str__(self):
        text = "{:>3d} ".format(self.idx)
        text_len = len(text)
        for n, probe in enumerate(self.probes):
            text_probe = str(probe)
            if n:
                text += (text_len*" ")+text_probe
            else:
                text += text_probe
        text += "\n"
        return text


class Probe(object):
    """
    Abstraction of a probe in a traceroute.
    """
    def __init__(self, name=None, ip=None, asn=None, rtt=None, annotation=None):
        self.name = name
        self.ip = ip
        self.asn = asn  # Autonomous System number
        self.rtt = rtt  # RTT in ms
        self.annotation = annotation  # Annotation, such as !H, !N, !X, etc

    def __str__(self):
        text = ""
        if self.asn is not None:
            text += "[AS{:d}] ".format(self.asn)
        #if self.rtt:
        #    text += "{:s} ({:s}) {:1.3f} ms".format(self.name, self.ip, self.rtt)
        if self.rtt:
            text += "{} ({}) {:1.3f} ms".format(self.name, self.ip, self.rtt)
        else:
            text = "*"
        if self.annotation:
            text += " {:s}".format(self.annotation)
        text += "\n"
        return text


def loads(data):
    """Parser entry point. Parses the output of a traceroute execution"""

    # Remove empty lines
    lines = [line for line in data.splitlines() if line != ""]

    # Get headers
    match_dest = RE_HEADER.search(lines[0])
    if not match_dest:
        raise InvalidHeader
    dest_name = match_dest.group(1)
    dest_ip = match_dest.group(2)

    # The Traceroute node is the root of the tree
    traceroute = Traceroute(dest_name, dest_ip)

    # Parse the remaining lines, they should be only hops/probes
    for line in lines[1:]:
        hop_match = RE_HOP.match(line)
        # Skip empty or non matching liners
        if not line or hop_match is None:
            continue

        if hop_match.group(1):
            hop_index = int(hop_match.group(1))
        else:
            hop_index = None

        if hop_index is not None:
            hop = Hop(hop_index)
            traceroute.add_hop(hop)


        hop_string = hop_match.group(2)

        probe_asn_match = RE_PROBE_ASN.search(hop_string)
        if probe_asn_match:
            probe_asn = int(probe_asn_match.group(1))
        else:
            probe_asn = None

        probe_name_ip_match = RE_PROBE_NAME_IP.search(hop_string)
        if probe_name_ip_match:
            probe_name = probe_name_ip_match.group(1)
            probe_ip = probe_name_ip_match.group(2) or probe_name_ip_match.group(3)
        else:
            # Let's try to only get IP (happens on windows)
            probe_ip_match = RE_PROBE_IP_ONLY.search(hop_string)
            if probe_ip_match:
                probe_name = probe_ip_match.group(1)
                probe_ip = probe_ip_match.group(1)
            else:
                probe_name = None
                probe_ip = None

        probe_rtt_annotations = RE_PROBE_RTT_ANNOTATION.findall(hop_string)

        for probe_rtt_annotation in probe_rtt_annotations:
            if probe_rtt_annotation[0]:
                probe_rtt = Decimal(probe_rtt_annotation[0])
            elif probe_rtt_annotation[1]:
                probe_rtt = None
            else:
                message = "Expected probe RTT or *. Got: '{}'".format(probe_rtt_annotation[0])
                raise Exception(message)

            probe_annotation = probe_rtt_annotation[2] or None

            probe = Probe(
                name=probe_name,
                ip=probe_ip,
                asn=probe_asn,
                rtt=probe_rtt,
                annotation=probe_annotation
            )
            hop.add_probe(probe)

    return traceroute


def load(data):
    return loads(data.read())


class ParseError(Exception):
    pass

class InvalidHeader(ParseError):
    pass
