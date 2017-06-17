#!/usr/bin/env python3
'''
This script is used to add the IP address to the /etc/hosts file.
It will retrieve the hostname using SNMP from the device.
It will check if the entry already exists or if it is faulty. It will adjust
the entry accordingly.
'''

import argparse
import os
import threading
import time
from queue import Queue
# import copy

from mylib import libbart as lb


def nameip(ip):
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    global hostdict

    try:
        sw = lb.Switch(ip, timeout=args.timeout)
        hostname = sw.gethostname()
    except ConnectionError as err:
        print("Couldn't get data from this IP:", ip, err)
        return
    else:
        hostdict[ip] = hostname


def threader():
    while True:
        # Getting the ip address out of the queue
        worker = q.get()
        if worker is None:
            break
        # starting the other function which does the work
        nameip(worker)
        # completed with the job
        q.task_done()


# Provide switches to control this script
parser = argparse.ArgumentParser(
    description='''
    This program is used to retrieve the management IP address and add it to
    the /etc/hosts file, to be able to use the hostname instead of the IP
    address to connect to the devices.
    ''',
    epilog="Bash environment variables used: CISCOCOMMUNITY")
parser.add_argument(
    '-i', '--ip', required=True, help='''Input should be an IP address, a file
    containing IP addresses or an HPov csv export file.''')
parser.add_argument(
    '-of', '--outputfile', required=False, default='/etc/hosts',
    help="Provide the output filename.")
parser.add_argument('--timeout', required=False, type=int, default=2,
                    help='''Provide an alternative timeout.
                    Default is %(default)s.''')
args = parser.parse_args()

# Starting with variables
start = start = time.time()
# communitystring = lb.envvariable("CISCOCOMMUNITY")
iplist, iperror = lb.readipfile(args.ip)
# today = time.strftime("%Y%m%d")
q = Queue()
threads = list()
# lock = threading.Lock()
processes = 30
hostdict = dict()
removeline = set()

# Staring an x amount of threads
for x in range(processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

# Putting the IP addresses in the queues
for ip in iplist:
    # Putting the ip in the queue
    q.put(ip)

# print('all jobs sent:', time.time() - start)

# wait until the thread terminates
q.join()

# stop workers
for i in range(processes):
    q.put(None)
for t in threads:
    t.join()

# print('Stopped all workers:', time.time() - start)

if os.path.isfile(args.outputfile):
    with open(args.outputfile, 'r') as f:
        currenthosts = f.readlines()

    hostlist = ['{} {}\n'.format(ip, hostdict[ip]) for ip in hostdict]

    for line in currenthosts:
        if line in hostlist:
            del hostdict[line.split()[0]]

    for line in currenthosts:
        if line[0].isdigit():
            for ip in hostdict:
                if hostdict[ip] in line:
                    removeline.add(line)
                # To make sure the ending includes a space, so the ending
                # on a .1 will not match a .10
                elif '{} '.format(ip) in line:
                    removeline.add(line)

# print('Read the outputfile:', time.time() - start, '\n' )

if hostdict or removeline:
    with open(args.outputfile, 'w') as f:
        for line in currenthosts:
            if line not in removeline:
                f.write(line)
            else:
                print('Entry has been removed:', line.rstrip('\n'))
        maxlength = lb.maxlength(hostdict)
        maxlengthvalue = lb.maxlength(hostdict.values())
        for ip in hostdict:
            print('{1:<{0}}  {3:<{2}} has been added'.format(
                maxlength, ip, maxlengthvalue, hostdict[ip]))
            f.write('{} {}\n'.format(ip, hostdict[ip]))

# print('\nWrote the outputfile:', time.time() - start, '\n')

if iperror:
    print("\nThe following lines from the source were not used because of " +
          "errors:\n")
    for x in iperror:
        print(x)
