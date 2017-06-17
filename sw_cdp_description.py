#!/usr/bin/env python3
'''This program is used to verify the descriptions of interfaces with CDP
neighbors. The information is retrieved via SNMP and the live information is
verified against the description. If it doesn't match, a new configuration is
created which can be used to update the switch configuration.

Bash environment variables used:
- CISCOCOMMUNITY
'''
import argparse
import os
import re
import shlex
import subprocess
import sys
import threading
import time
from queue import Queue

from hnmp import SNMP, ipv4_address

from mylib import libbart as lb


# Useful information:
# http://www.oidview.com/mibs/0/IF-MIB.html
# http://www.oidview.com/mibs/9/CISCO-VLAN-MEMBERSHIP-MIB.html
# https://slaptijack.com/networking/finding-cisco-neighbors-with-snmp/
# http://snmp.cloudapps.cisco.com/Support/SNMP/do/BrowseMIB.do?local=en&step=2&mibName=CISCO-CDP-MIB
# http://www.oidview.com/mibs/9/CISCO-CDP-MIB.html
# http://www.oidview.com/mibs/0/IEEE8023-LAG-MIB.html
# https://github.com/trehn/hnmp/blob/master/hnmp.py
# https://regex101.com/#python

def getRemotePC(remoteip, remoteintf):
    '''A module to retrieve the remote Port-Channel name.'''
    global errorlist
    ifindex = None
    remponameshort = None
    snmprem = SNMP(remoteip, community=communitystring, timeout=timeout)
    mib = '1.3.6.1.2.1.2.2.1'
    remport_info = {}
    remport_info = snmprem.table(
        mib,
        columns={
            1: "ifIndex",
            2: "ifDescr",
        },
        fetch_all_columns=False,
    )
    if remport_info.columns:
        # Find the index value of the specific interface.
        # Get the location of the specific interface.
        intfloc = remport_info.columns['ifDescr'].index(remoteintf)
        # Get the ifindex number of the specific interface
        ifindex = str(remport_info.columns['ifIndex'][intfloc])
        # print ('intfloc:', intfloc)
        # print ('ifindex:', ifindex)
    else:
        errorlist.append(
            '{} {} to {} {}: Can\'t retrieve the SNMP values.'.format(
                ip, ownintfshort, remoteip, remoteintf))
        # print('can\'t retrieve the SNMP index values:', remoteintf)
        # continue
    #
    rempooid = snmprem.get(
        '1.2.840.10006.300.43.1.2.1.1.12.{}'.format(ifindex))
    # find the port-channel name
    remponameshort = snmprem.get('1.3.6.1.2.1.31.1.1.1.1.{}'.format(rempooid))
    return remponameshort


def getownintfanddesc(snmp, intf):
    # Get your own interface.
    ownintfshort = snmp.get('1.3.6.1.2.1.31.1.1.1.1.{}'.format(intf))
    # current description
    ownintfdesc = snmp.get('1.3.6.1.2.1.31.1.1.1.18.{}'.format(intf))
    return ownintfshort, ownintfdesc


def getremoteintfshort(snmp, intf, intfsub):
    remoteintf = snmp.get('1.3.6.1.4.1.9.9.23.1.2.1.1.7.{}.{}'.format(intf,
                                                                      intfsub))
    remoteintfshort = '{}{}'.format(
        remoteintf[0:2], remoteintf.split('thernet')[1])
    return remoteintf, remoteintfshort


def getswinfo(intf, intfsub, remoteintf, remotehostname, snmp, pcdict):
    '''A module to retrieve the local and CDP information on a per
    interface/neighbor basis'''
    # make sure all variable exists
    remponameshort = None
    roam = None
    # notsw,pooid = None,None
    # roam,roammatch = None,None
    #
    # Check if this interface is part of a port-channel
    pooid = snmp.get('1.2.840.10006.300.43.1.2.1.1.12.{}'.format(
        intf))
    #
    # CDP information for remote system
    remotehw = snmp.get('1.3.6.1.4.1.9.9.23.1.2.1.1.8.{}.{}'.format(intf,
                                                                    intfsub))
    # Exclude some hardware
    notsw = reNOTSW.search(remotehw)
    if notsw:
        roam = True
    #
    if pooid:
        # Get the Shortname of the PC, if it the interface was part of the
        # port-channel
        # ponameshort = snmp.get( '1.3.6.1.2.1.31.1.1.1.1.{}'.format(pooid))
        # print('ponameshort:', ponameshort)
        remoteip = ipv4_address(snmp.get(
            '1.3.6.1.4.1.9.9.23.1.2.1.1.4.{}.{}'.format(intf, intfsub)))
        remponameshort = getRemotePC(remoteip, remoteintf)
        if remponameshort:
            # Create a port-channel dict. {'localPo index#':'remhostname
            # remPo'}
            pcdict[pooid] = '{} {}'.format(remotehostname, remponameshort)
        else:
            pcdict[pooid] = '{}'.format(remotehostname)
    #
    return remponameshort, roam, pcdict


def snmpcdp(ip):
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    # s1 = time.time()
    configlist = []
    pcdict = {}
    # New solution, using subprocess to start linux commands
    snmp_mib = '1.3.6.1.4.1.9.9.23.1.2.1.1.6'
    snmp = SNMP(ip, community=communitystring, timeout=timeout)
    # snmp = SNMP(ip, community=communitystring)
    #
    try:
        hostname = snmp.get('1.3.6.1.4.1.9.2.1.3.0')
    except:
        print('Couldn\'t access the device via SNMP. IP: {}'.format(ip))
        return 'Timeout occured'

    # Use the snmpwalk command to get the CDP remote hostname and
    # also the index
    # numbers which are required for other snmp.gets.
    # snmpwalk is used, since the interface index numbers are not provided
    # in the CDP table.
    # cmd = 'snmpwalk -m+CISCO-CDP-MIB -v2c -c {} {} {}'.format(
    cmd = 'snmpwalk -v2c -c {} {} {}'.format(
        communitystring, ip, snmp_mib)
    args = shlex.split(cmd)
    output = subprocess.Popen(
        args,
        stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    #
    for line in output.split('\n'):
        # print ('line:', line)
        # Skip empty lines
        if not line:
            continue
        #
        # Get the index number from the snmpwalk to use as interface indication
        # intf = line.split('.')[1]
        intf = line.split()[0].split('.')[-2]
        # A number behind it, needed for the CDP SNMP table
        intfsub = line.split()[0].split('.')[-1]
        #
        # Get the remote hostname from the line
        remotehostname = line.split('"')[1].split('.')[0]
        #
        # Matching is done on the hostnames of the remote devices.
        if rePHONE.search(line):
            continue
        elif reAP.search(line):
            ownintfshort, ownintfdesc = getownintfanddesc(snmp, intf)
            newdesc = 'access-point'
        elif reWLC.search(line):
            if skipwlc:
                continue
            # print ('wlcmatch:', wlcmatch)
            ownintfshort, ownintfdesc = getownintfanddesc(snmp, intf)
            remoteintf, remoteintfshort = getremoteintfshort(
                snmp, intf, intfsub)
            if remotehostname.endswith('CW001-Standby'):
                remotehostname = remotehostname.replace(
                    'CW001-Standby', 'CW002')
            newdesc = '{} {}'.format(remotehostname, remoteintfshort)
        elif reDSI.search(line):
            continue
            # print ('dsimatch:', dsimatch)
            # print ('DSI part is progress\n')
            ownintfshort, ownintfdesc = getownintfanddesc(snmp, intf)
            remoteintf, remoteintfshort = getremoteintfshort(
                snmp, intf, intfsub)
            # print (remotehostname)
            # newdesc = '{} {}'.format(remotehostname, remoteintfshort)
            # configlist.append(
            # 'interface {}\n ! old: {}\n no cdp enable\n!'.format(
            #                ownintfshort, ownintfdesc))
            # continue
        elif reWAN.search(line) or reVG.search(line):
            ownintfshort, ownintfdesc = getownintfanddesc(snmp, intf)
            remoteintf, remoteintfshort = getremoteintfshort(
                snmp, intf, intfsub)
            newdesc = '{} {}'.format(remotehostname, remoteintfshort)
        elif reWAAS.search(line):
            ownintfshort, ownintfdesc = getownintfanddesc(snmp, intf)
            remoteintf, remoteintfshort = getremoteintfshort(
                snmp, intf, intfsub)
            remoteintfshort = remoteintfshort.replace(' ', '')
            newdesc = '{} {}'.format(remotehostname, remoteintfshort)
        elif reSW.search(line):
            ownintfshort, ownintfdesc = getownintfanddesc(snmp, intf)
            remoteintf, remoteintfshort = getremoteintfshort(
                snmp, intf, intfsub)
            remponameshort, roam, pcdict = getswinfo(
                intf, intfsub, remoteintf, remotehostname, snmp, pcdict)
            # If this is a roaming switch, it is ignored further
            roammatch = reROAM.search(ownintfdesc)
            if roam or roammatch:
                errorlist.append(
                    'ip: {}, interface: {}\
                    \nRoaming switches ignored.\n{}'.format(
                        ip, ownintfshort, line))
                continue
            #
            # How should the description look like:
            # Physical interface
            if remotehostname and remoteintfshort and remponameshort:
                newdesc = '{} {} {}'.format(
                    remotehostname, remoteintfshort, remponameshort)
            elif remotehostname and remoteintfshort:
                # If there is no port-channel related to the interface
                newdesc = '{} {}'.format(
                    remotehostname, remoteintfshort)
            else:
                print('something went wrong.\nLine:', line)
                continue
            #
        else:
            print("OTHER:\tString: {}".format(line.split('"')[1]))
            continue
        #
        if not ownintfdesc == newdesc:
            # print ('IP: {} interface: {}, remotehostname {}'.format(
            #        ip,ownintfshort,remotehostname))
            # print ('!       old:', ownintfdesc)
            # print (' description', newdesc)
            configlist.append(
                'interface {}\n!       old: {}\n description {}\n!'.format(
                    ownintfshort, ownintfdesc, newdesc))
    #
    pclist = []
    for x in pcdict:
        pcintfdesc = snmp.get('1.3.6.1.2.1.31.1.1.1.18.{}'.format(x))
        pcintfshortname = snmp.get('1.3.6.1.2.1.31.1.1.1.1.{}'.format(x))
        if not pcintfdesc == pcdict[x]:
            # print ('IP: {}, interface: {}'.format(ip,pcintfshortname))
            pclist.append(
                'interface {}\n!       old: {}\n description {}\n!'.format(
                    pcintfshortname, pcintfdesc, pcdict[x]))
            # else:
            #    print ('%s: is good' % pcintfshortname)
        # Write the config to a file
    if configlist or pclist:
        if not os.path.isdir(outputdir):
            os.mkdir(outputdir)
        filename = '{}{}_{}_config.txt'.format(outputdir, hostname, ip)
        with open(filename, 'a') as f:
            f.write('! Hostname: {}, IP: {}\n!\n'.format(hostname, ip))
            for x in configlist:
                f.write('{}\n'.format(x))
            for x in pclist:
                f.write('{}\n'.format(x))
    else:
        print('{}, {}: descriptions are in perfect shape.'.format(
            hostname, ip))
    #
    # print ("\n\nTotal time per IP: ", ip, time.time() - s1)

    # ########### End of function ########


def threader():
    while True:
        # Getting the ip address out of the queue
        worker = q.get()
        if worker is None:
            break
        # starting the other function which does the work
        snmpcdp(worker)
        # completed with the job
        q.task_done()


# Provide switches to control this script
parser = argparse.ArgumentParser(
    # usage="%(prog)s [options] ; Use -h to show all options.",
    add_help=True,
    description='''
    This program is used to verify the descriptions of interfaces with CDP
    neighbors. The information is retrieved via SNMP and the live information
    is verified against the description. If it doesn't match, a new
    configuration is created which can be used to update the switch
    configuration.
    ''',
    epilog="Bash environment variables used: CISCOCOMMUNITY")
# parser.add_argument('-h', '--help', action='help',
#    help='Show this help message and exit.')
parser.add_argument('-i', '--ip', required=True, help="Input should \
be an IP address, a file containing IP addresses or an HPov csv export \
file.")
parser.add_argument('--skipwlc', required=False, action='store_const',
                    const='yes',
                    help="Set this if you want to skip the WLC checks.")
args = parser.parse_args()

arg1 = args.ip
communitystring = lb.envvariable("CISCOCOMMUNITY")
iplist, iperror = lb.readipfile(arg1)
# today = time.strftime("%Y%m%d")
timeout = 1
q = Queue()
threads = list()
lock = threading.Lock()
processes = 30
errorlist = []
skipwlc = None
if args.skipwlc:
    skipwlc = args.skipwlc

# Test ip
# ip='10.207.137.254'

# RE for switch hostnames
reSW = re.compile('(SW\d{4,6}'
                  '|[A-Z]{5}[0-9]{2}-[IO]-CR[0-9]{3}'
                  '|[A-Z]{5}[0-9]{2}-[IO]-AS[0-9]{3})')

# RE for WLC hostnames
reWLC = re.compile('(WLC\d{4,6}'
                   '|[A-Z]{5}[0-9]{2}-[IO]-CW[0-9]{3}'
                   '|[A-Z]{5}[0-9]{2}-WLC[0-9]{2})')

# RE for DSI
reDSI = re.compile('(rfc[a-z]{3}[ab]sw[0-9]{2})')

# RE for roaming
reROAM = re.compile('(roam)', re.IGNORECASE)
reNOTSW = re.compile('(-8TC-L)', re.IGNORECASE)
reWLCsec = re.compile('CW001-Standby', re.IGNORECASE)
reAP = re.compile('(AP[a-z0-9]{4}\.[a-z0-9]{4}\.[a-z0-9]{4}'
                  '|[A-Z]{5}[0-9]{2}-AP[0-9]{2,3}'
                  '|[A-Z]{5}[0-9]{2}-[0-9]-AP[0-9]{2,3}'
                  '|AP\d{4,6})', re.IGNORECASE)
reWAN = re.compile('campin-[a-z]{5}\d{2}[ps]-\d*', re.IGNORECASE)
reWAAS = re.compile('WAE-[a-z]{5}\d{2}-\d', re.IGNORECASE)
reVG = re.compile('VG[0-9]{4,6}', re.IGNORECASE)
rePHONE = re.compile('SEP[a-z0-9]{12}', re.IGNORECASE)


# Staring an x amount of threads
for x in range(processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

# Start the clock
start = time.time()

if iplist:
    # totalip = len(iplist)
    workdir = os.path.expanduser('~') + '/working'
    currenttime = time.strftime("%Y%m%d_%H%M%S")
    outputdir = workdir + "/" + currenttime + "_description" + "/"
else:
    sys.exit("No valid IPs.")


# Putting the IP addresses to the queue
for ip in iplist:
    q.put(ip)

# wait until the thread terminates
q.join()

# stop workers
for i in range(processes):
    q.put(None)
for t in threads:
    t.join()

# Show all errors, on screen only
if errorlist:
    print('\n\nList of roaming switches and/or errors:')
    for x in errorlist:
        print('{}\n'.format(x))
if iperror:
    print('\n\nIP\'s or lines not used:')
    for x in iperror:
        print('{}\n'.format(x))

# end time - start time
print("\n\nTotal time:", time.time() - start)
if os.path.isdir(outputdir):
    print("The output is saved in:\n", outputdir)
else:
    print("Nothing is written.")
