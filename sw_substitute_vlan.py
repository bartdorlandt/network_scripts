#!/usr/bin/env python3
'''
This script is meant to reconfigure a lot of ports to use a standard
configuration. It is equiped with prebuild standards, like dot1x and
monitor. Both used for the ISE project and future.
'''
import argparse
import glob
import os
import threading
import time
from queue import Queue

from mylib import libbart as lb


# Creating the funcions
def threader():
    while True:
        # Getting the value out of the queue
        worker = q.get()
        if worker is None:
            break
        # starting the other function which does the work
        swsubstitute(worker)
        # completed with the job
        q.task_done()


# The function that will get the sh run and extract the L2 and L3 lists to use
# to create the new configuration.
def swsubstitute(ip):
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    # Get the hostname
    try:
        sw = lb.Switch(ip, acsprefix=acsprefix, delay_factor=delay)
        hostname = sw.gethostname()
    except ConnectionError as err:
        print('SNMP error:', ip, err)
        return

    # result is used to save the configuration
    result = []
    #
    print("Starting with ip:", ip)
    shrun = lb.getcmdoutput(ip, 'sh run', delay_factor=delay,
                            device=devicetype,
                            acsprefix=acsprefix)
    l2, l3 = lb.getvlanports(shrun, args.oldvlan)
    # Layer 2 vlans
    if l2 or l3:
        if not os.path.isdir(outputdir):
            os.mkdir(outputdir)
        result.append('! Configuration for {}'.format(ip))

    for x in l2:
        if setdefaultIF:
            result.append('default {}'.format(x))
        result.append(x)
        if args.prebuilt == 'dot1x':
            result.append(dot1xif)
        elif args.prebuilt == 'monitor':
            result.append(monitordot1x)

    # if l3:
    #     result.append('\n')
    #     result.append('''! create a l3 loop to change the vlan number,
    #                   but keep the configuration.''')

    # for x in l3:
    #     result.append(x)
        # Do a for loop over the template file or an integrated port template.

    filename = outputdir+hostname+"_"+ip+"_config.txt"
    outputfile = open(filename, 'w')
    for x in result:
        outputfile.write(x)


# Starting the actual code. Starting with argparse
parser = argparse.ArgumentParser(
    add_help=True,
    description='''This script is used to convert all interfaces belonging to
    a certain vlan number, to a new vlan. It includes both access ports and
    L3 vlans.

Be aware that this could add to and overwrite an existing vlan.''',
    epilog="Bash environment variables used: ACSUSER, ACSPASS")
parser.add_argument(
    '-i', '--ip', required=True, help='''Input should be an
IP address, a file containing IP addresses or an HPov csv export file.''')
parser.add_argument(
    '-ov', '--oldvlan', type=int, required=True,
    help='The old vlan number.')
parser.add_argument(
    '--delay', required=False, type=float, default=1.0,
    help='''Provide an alternative delay factor. Default is %(default)s.''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
parser.add_argument('--telnet', default=None, required=False,
                    action='store_true', help='''Use telnet instead of SSH.''')
# Multual exclusive group Only one of the following can be selected.
group = parser.add_mutually_exclusive_group(required=True)
# group.add_argument(
#    '-nv', '--newvlan', type=int, help='The new vlan number.')
group.add_argument(
    '-pb', '--prebuilt', choices=['dot1x', 'monitor'],
    help='The choices of the prebuilt templates.')
args = parser.parse_args()

if args.prebuilt in ['dot1x']:
    setdefaultIF = True

dot1xif = '''
 description 802.1x
 switchport mode access
 authentication control-direction in
 authentication event server alive action reinitialize
 authentication host-mode multi-domain
 authentication order mab dot1x
 authentication priority dot1x mab
 authentication port-control auto
 authentication periodic
 authentication timer reauthenticate 7200
 authentication timer inactivity 3600
 mab
 snmp trap mac-notification change added
 snmp trap mac-notification change removed
 dot1x pae authenticator
 dot1x timeout quiet-period 300
 dot1x timeout ratelimit-period 300
 spanning-tree portfast
'''

monitordot1x = '''
 authentication host-mode multi-domain
 authentication open
 authentication port-control auto
 mab
 dot1x pae authenticator
 authentication order mab dot1x
 authentication priority dot1x mab
'''

# Setting global variables
delay = args.delay
acsprefix = args.acsprefix
devicetype = 'cisco_ios'
q = Queue()
threads = list()
# lock = threading.Lock()
currenttime = time.strftime("%Y%m%d_%H%M%S")
processes = 30
searchstring = "*config.txt"
iplist, iperror = lb.readipfile(args.ip)
workdir = os.path.expanduser('~') + '/working'
outputdir = workdir + "/" + currenttime + "_vlan" + "/"
if args.telnet:
    devicetype = 'cisco_ios_telnet'

# Creating the sub-directory to save the files
if not os.path.isdir(outputdir):
    os.mkdir(outputdir)

# Staring an x amount of threads
for x in range(processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

print("Total IPs:", len(iplist))
if iperror:
    print("Total errors:", len(iperror))
    print("\n\nThe following lines from the source were not used because of \
errors:\n")
    for x in iperror:
        print(x)

# Doing some time calculation
start = time.time()

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

# Only listing the output directory if there is actually something.
files = (glob.glob1(outputdir, searchstring))
print("\nTotal time after input:", time.time() - start)
if not len(files) == 0:
    print("Total output files: {}. The output is saved in:".format(len(files)))
    print("    ", outputdir)
