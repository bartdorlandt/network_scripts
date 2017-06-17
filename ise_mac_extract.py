#!/usr/bin/env python3
import argparse
import os
import re
import sys
import time

from mylib import libbart as lb


# Provide switches to control this script
parser = argparse.ArgumentParser(
    description='''This script is used to extract the MAC addresses and
    provide an output file to be used to import in ISE. It is expected that
    the layer 3 switch ip address is provided.
    ''',
    epilog="Bash environment variables used: ACSUSER, ACSPASS")
parser.add_argument(
    '-i', '--ip', required=True,
    help='''Input should be an IP address, a file containing IP addresses
    or an HPov csv export file. Only the first IP address is used.''')
parser.add_argument(
    '--vrf', '--vrffile', required=True, default=None,
    help='''Provide the input file containing the VRF's.''')
parser.add_argument(
    '--vlan', '--vlanfile', required=True, default=None,
    help='''Provide the input file containing the VLAN's. It lists which vlans
    are used and how they are named.''')
parser.add_argument(
    '--l2vlan', '--l2vlanfile', required=True, default=None,
    help='''Provide the input file containing the L2 VLAN's. It lists which
    vlans are used and how they are named.''')
parser.add_argument(
    '-of', '--outputfile', default=None,
    help='''Provide the output filename if desired, else it will be printed
    on screen.''')
parser.add_argument(
    '--delay', required=False, type=float, default=1.0,
    help='''Provide an alternative delay factor. Default is %(default)s.''')
parser.add_argument(
    '--noinfo', required=False, action='store_false', default=True,
    help='No information will be printed on the screen. Useful for the ' +
    'cronjobs.')
parser.add_argument(
    '--acsprefix', required=False, default=None,
    help='''Provide a prefix to read a different set of
    environemnt variables than the default.''')
args = parser.parse_args()

# Variables
arg1 = args.ip
iplist, iperror = lb.readipfile(arg1)
ip = iplist[0]

if not os.path.isfile(args.vrf):
    sys.exit("The vrf file doesn't exist")
if not os.path.isfile(args.vlan):
    sys.exit("The vlan file doesn't exist")
if not os.path.isfile(args.l2vlan):
    sys.exit("The l2 vlan file doesn't exist")

# Start the script, get the info required
start = time.time()

# create a dictionary of vlan and names for used vlans
# create the cmd file to be send to the switch.
vlandict = {}
with open(args.vlan, 'r') as a, open(args.l2vlan, 'r') as b:
    f = a.readlines() + b.readlines()
    for line in f:
        if not line[0].isdigit():
            continue
        vlan = line.split()[0]
        vlanname = line.split()[1]
        if vlanname:
            # if vlanname == 'noscan':
            #    continue
            # vrf = line.split()[1]
            vlandict[vlan] = vlanname
#        if vrf == 'NONVRF':
#            cmd = '{}sh ip arp vlan {}\n'.format(cmd, vlan)
#        else:
#            cmd = '{}sh ip arp vrf {} vlan {}\n'.format(cmd, vrf, vlan)
        else:
            sys.exit('vlan or vlanname not correctly provided')
#
#
try:
    sw = lb.Switch(ip, acsprefix=args.acsprefix)
    hostname = sw.gethostname()
except ConnectionError as err:
    # print('SNMP error:', ip, err)
    sys.exit('SNMP error:', ip, err)
#

# Create the vrflist
startwith = re.compile('^[A-Z]')
with open(args.vrf, 'r') as f:
    vrflist = [x.replace('\n', '') for x in f if startwith.match(x)]

# Create the command list
cmd = 'sh ip arp\n'
for vrf in vrflist:
    cmd = cmd + 'sh ip arp vrf ' + vrf + '\n'

# Get the output of all the arp commands per vrf in one go.
if args.noinfo:
    print('sending the commands to the switch', time.time() - start)
arplist = lb.getcmdoutput(ip, cmd, acsprefix=args.acsprefix,
                          delay_factor=args.delay).split('\n')
if args.noinfo:
    print('got the configuration from the switch', time.time() - start)

# RE
arp = re.compile('Internet +\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} +\d+ +\
([0-9a-z]{4}\.[0-9a-z]{4}\.[0-9a-z]{4}) +ARPA +Vlan(\d+)')

# Output information
if args.outputfile:
    filename = args.outputfile
else:
    filename = '{}/{}_{}_{}_macs.txt'.format(
        os.path.dirname(os.path.abspath(args.vlan)),
        os.path.basename(args.vlan).split('_')[0],
        hostname,
        iplist[0])

# check for existing information. Do not add additional mac addresses
if args.noinfo:
    print('reading the existing file (if any) and creating a tuple',
          time.time() - start)
if os.path.isfile(filename):
    with open(filename, 'r') as f:
        existmac = [x.split(',')[0] for x in f]
        mactuple = tuple(existmac)
else:
    mactuple = ()
if args.noinfo:
    print('done with the file', time.time() - start)

outputfile = open(filename, 'a')

# count = 0
for line in arplist:
    inclmac = arp.search(line)
    if not inclmac:
        continue
    elif vlandict[inclmac.group(2)] == 'noscan':
        continue
    elif inclmac.group(1) in mactuple:
        continue
    else:
        # print ('{},,{}'.format(inclmac.group(1), vlandict[inclmac.group(2)]))
        outputfile.write(
            '{},,{}\n'.format(inclmac.group(1), vlandict[inclmac.group(2)]))
#    count += 1

outputfile.close()

# print(count)
if args.noinfo:
    print("\nTotal time after input:", time.time() - start)
