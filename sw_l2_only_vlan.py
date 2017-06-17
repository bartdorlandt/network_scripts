#!/usr/bin/env python3
'''
This scripts logs into the switch and does a diff between the L3 and L2 vlans.
It will show a list of L2 vlans that don't exist as L3.
Bash environment variables used:
- ACSUSER
- ACSPASS
'''
import argparse

from mylib import libbart as lb


# Provide switches to control this script
parser = argparse.ArgumentParser(
    description='''This program is used to compare the L3 and L2 vlans
    of a core switch ''',
    epilog="""Bash environment variables used: ACSUSER, ACSPASS,
    CISCOCOMMUNITY""")
parser.add_argument(
    '-i', '--ip', required=True, help="This is the L3 switch' IP address.")
parser.add_argument('--delay', required=False, type=float, default=1.0,
                    help='''Provide an alternative delay factor.
                    Default is %(default)s.''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
parser.add_argument('--telnet', default=None, required=False,
                    action='store_true', help='''Use telnet instead of SSH.''')
args = parser.parse_args()

delay = args.delay
acsprefix = args.acsprefix
devicetype = 'cisco_ios'
iplist, iperror = lb.readipfile(args.ip)
l2vlanlist = []
l3vlanlist = []
if args.telnet:
    devicetype = 'cisco_ios_telnet'

cmd = ['sh ip int brie | i ^Vlan', 'sh vlan br']
l2only = lb.l2_only_vlans(iplist[0], acsprefix=acsprefix, delay_factor=delay,
                          device=devicetype)

print('These vlans are only L2:', l2only)
