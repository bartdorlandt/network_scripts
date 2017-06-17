#!/usr/bin/env python3
import argparse
import threading
from queue import Queue

from mylib import libbart as lb


def threader():
    while True:
        # Getting the ip address out of the queue
        worker = q.get()
        if worker is None:
            break
        # print("Worker is: ", worker)
        # starting the other function which does the work
        mainfunction(worker)
        # completed with the job
        q.task_done()


def getvlans(ip):
    # Loading the sh int status
    vlans = set()
    status = lb.getcmdoutput(ip, 'sh int status',
                             delay_factor=delay,
                             device=devicetype,
                             acsprefix=acsprefix)
    if not status:
        print("!\n! SSH not active. IP: {}\n".format(ip))

    for x in status.split('\n'):
        vlan = x[42:48].rstrip()
        if not vlan:
            # print ('not vlan')
            continue
        elif x.startswith('Po'):
            # print ('Start with Po.\n{}'.format(x))
            continue
        elif vlan == 'trunk' or vlan == 'routed':
            continue
        elif "Not Present" in x or "SFP" in x:
            continue
        elif "VG" in x:
            continue
        elif vlan[0].isdigit():
            # print ('vlan added {}'.format(vlan))
            vlans.add(int(vlan))
        else:
            print('Nothing done with {}, \n  IF: {}'.format(ip, x))
    return vlans


def mainfunction(ip):
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    # Get all the unique vlans
    vlans = getvlans(ip)

    # Get the hostname and devices via SNMP.
    try:
        sw = lb.Switch(ip, acsprefix=acsprefix, delay_factor=delay)
        hostname = sw.gethostname()
    except ConnectionError as err:
        print('SNMP error:', ip, err)
        return
    else:
        dsw[ip] = (hostname, sorted(vlans))


# Provide switches to control this script
parser = argparse.ArgumentParser(
    description='''This script is used to get all the unique vlans of all the
    provided switches.''',
    epilog='''Bash environment variables used:
    CISCOCOMMUNITY, ACSUSER, ACSPASS''')
parser.add_argument(
    '-i', '--ip', required=True,
    help='''Input should be an IP address, a file containing IP addresses
    or an HPov csv export file.''')
parser.add_argument(
    '--delay', required=False, type=float, default=1.0,
    help='''Provide an alternative delay factor. Default is %(default)s.''')
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
iplist, iperror = lb.readipfile(args.ip)
dsw = dict()
globalvlans = set()
processes = 30
q = Queue()
threads = list()
lock = threading.Lock()
if args.telnet:
    devicetype = 'cisco_ios_telnet'

# Staring an x amount of threads
for x in range(processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

print("Total IPs:", len(iplist))
# print(iplist)
if iperror:
    print("Total errors:", len(iperror))
    print('''\n\nThe following lines from the source were not used because of
errors:\n''')
    for x in iperror:
        print(x)

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

# Print the information
for x in sorted(dsw.keys(), key=lb.split_ip):
    print('{:<15}  {:<8}  vlans: {}'.format(x, dsw[x][0], ', '.join(
        map(str, dsw[x][1]))))
    for y in dsw[x][1]:
        globalvlans.add(int(y))

print('\nAll unique vlans: {}'.format(
    ', '.join(map(str, sorted(globalvlans)))))
