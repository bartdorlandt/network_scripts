#!/usr/bin/env python3
'''
Do a sh mac addr vlan X on the core switch to find out which MAC addresses
exist for L2 vlans.
Bash environment variables used:
- ACSUSER
- ACSPASS
'''
import argparse
import sys
import os

from mylib import libbart as lb


# Provide switches to control this script
parser = argparse.ArgumentParser(
    description='''
    This script will get the L2 only vlan mac addresses. Based on an input
    vlan file.''',
    epilog="Bash environment variables used: ACSUSER, ACSPASS.")
parser.add_argument(
    '-i', '--ip', required=True, help="This is the L3 switch' IP address.")
parser.add_argument('-l2', '--l2vlan', required=True,
                    help='''The L2 vlan file.''')
parser.add_argument('--delay', required=False, type=float, default=1.0,
                    help='''Provide an alternative delay factor.
                    Default is %(default)s.''')
parser.add_argument('-of', '--outputfile', required=True, default=None,
                    help='''Provide the output filename.''')
parser.add_argument(
    '--noinfo', required=False, action='store_false', default=True,
    help='No information will be printed on the screen. Useful for the ' +
    'cronjobs.')
parser.add_argument(
    '--acsprefix', required=False, default=None,
    help='''Provide a prefix to read a different set of
    environemnt variables than the default.''')
args = parser.parse_args()

iplist, iperror = lb.readipfile(args.ip)
ip = iplist[0]
l2dict = {}
macdict = {}
cmd = 'sh mac address-table vlan '
cmdlist = []
filename = args.outputfile
# outputdir = '{}/ISE_SW/'.format(os.getenv("HOME"))
# outputfile = args.outputfile

with open(args.l2vlan, 'r') as f:
    for line in f:
        if line[0].isdigit() and not line.split()[1] == 'noscan':
            cmdlist.append('{}{}'.format(cmd, line.split()[0]))
            l2dict[line.split()[0]] = line.split()[1]

if not cmdlist:
    sys.exit('[-] No commands to send to the device. Exiting')

cmdoutput = lb.getcmdoutput(ip, cmdlist, acsprefix=args.acsprefix,
                            delay_factor=args.delay)

if not cmdoutput:
    sys.exit('No output received from the switch. Exiting')

for x in cmdoutput.split('\n'):
    if x.startswith('*'):
        macdict[x.split()[2]] = x.split()[1]
    elif 'dynamic' in x:
        macdict[x.split()[1]] = x.split()[0]

if os.path.isfile(filename):
    with open(filename, 'r') as f:
        existmac = [x.split(',')[0] for x in f]
        mactuple = tuple(existmac)
else:
    mactuple = ()

outputfile = open(filename, 'a')

for mac in macdict:
    if mac in mactuple:
        if args.noinfo:
            print('mac: {} already exists'.format(mac))
        continue
    else:
        # print('{},,{}'.format(mac, l2dict[macdict[mac]]))
        outputfile.write('{},,{}\n'.format(mac, l2dict[macdict[mac]]))
        if args.noinfo:
            print('mac: {} added to the file: {}'.format(mac, filename))

outputfile.close()
