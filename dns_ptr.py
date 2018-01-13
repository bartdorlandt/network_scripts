#!/usr/bin/env python3
"""
Create a list of arpa entries for DNS based on IP numbers provided.

No Bash environment variables used.
"""
import argparse

from mylib import libbart as lb


# Provide switches to control this script
parser = argparse.ArgumentParser(
    description="This program is used to provide a quick list of arpa PTR record entries.",
    epilog="No Bash environment variables used")
parser.add_argument('-i', '--ip', required=True, help='''Input should
be an IP address, a file containing IP addresses or an HPov csv export
#file.''')
args = parser.parse_args()

iplist, iperror = lb.readipfile(args.ip)

arpa = lb.atoptr(iplist)

for x in arpa:
    print(x)
