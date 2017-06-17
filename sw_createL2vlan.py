#!/usr/bin/env python3
import argparse
import os
import re
import sys

from mylib import libbart as lb


# Provide switches to control this script
parser = argparse.ArgumentParser(
    description='''
    This script is used to generate the configuration for L2 vlans. The output
    could be either printed to your screen, or saved to a file.
    ''',
    epilog="Bash environment variables used: CISCOCOMMUNITY")
parser.add_argument(
    '-i', '--ip', required=True,
    help='''Input should be an IP address, a file containing IP addresses
    or an HPov csv export file. Only the first IP address is used.''')
parser.add_argument(
    '-of', '--outputfile', default=None, action='store_true',
    help='''Provide the output filename if desired, else it will be printed
    on screen.''')
parser.add_argument('--delay', required=False, type=float, default=1.0,
                    help='''Provide an alternative delay factor.
                    Default is %(default)s.''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
parser.add_argument('--telnet', default=None, required=False,
                    action='store_true', help='''Use telnet instead of SSH.''')
args = parser.parse_args()

# Variables
delay = args.delay
acsprefix = args.acsprefix
devicetype = 'cisco_ios'
config = []
revlan = re.compile('(\d{1,4}) *(.+?) +?active')

arg1 = args.ip
iplist, iperror = lb.readipfile(arg1)
ip = iplist[0]

if args.telnet:
    devicetype = 'cisco_ios_telnet'

# Set outputdir if iplist exists, count total IPs
if ip:
    outputdir = os.path.expanduser('~') + '/working'
else:
    sys.exit("No IP")

# Start the script
output = lb.getcmdoutput(ip, 'sh vlan brief',
                         delay_factor=delay,
                         device=devicetype,
                         acsprefix=acsprefix).split('\n')
try:
    sw = lb.Switch(ip, acsprefix=acsprefix, delay_factor=delay)
    hostname = sw.gethostname()
except ConnectionError as err:
    print('SNMP error:', ip, err)
    return

# Filling the config list from the output
for vlan in output:
    vlanmatch = revlan.search(vlan)
    if vlanmatch:
        config.append('vlan {}\n name {}'.format(
            vlanmatch.group(1), vlanmatch.group(2)))

# create dir if needed
if not os.path.isdir(outputdir):
    os.mkdir(outputdir)

outputfile = '{}/{}_{}_l2vlan.txt'.format(outputdir, hostname, iplist[0])

if args.outputfile:
    if not os.path.isfile(outputfile):
        with open(outputfile, 'w') as f:
            f.write('!!!!! L2 vlan config !!!!!\n\n')
            for x in config:
                f.write(x + '\n')
        print('The configuration is saved in: {}'.format(outputfile))
    else:
        sys.exit('File already exists: {}'.format(outputfile))
else:
    print('\n!!!!! L2 vlan config !!!!!\n')
    for x in config:
        print(x)
