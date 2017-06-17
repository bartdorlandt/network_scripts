#!/usr/bin/env python3

import argparse
import os
import sys
import threading
import time
from queue import Queue
from netmiko import ConnectHandler
from netmiko.ssh_exception import (NetMikoTimeoutException,
                                   NetMikoAuthenticationException)

from mylib import libbart as lb


def threader():
    while True:
        # Getting the ip address out of the queue
        worker = q.get()
        if worker is None:
            break
        # starting the other function which does the work
        execute(worker)
        # completed with the job
        q.task_done()


def execute(ip):
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    result = []
    # for each ip we will send the configuration command(s).
    device = {
        'device_type': 'cisco_ios',
        'ip': ip,
        'username': acsuser,
        'password': acspass,
        'secret': acsenable,
        'verbose': False,
        'global_delay_factor': delay_factor,
    }

    try:
        net_connect = ConnectHandler(**device)
    except NetMikoTimeoutException as e:
        print("Timeout Error:", ip, e)
        return None
    except NetMikoAuthenticationException as e:
        print("Authentication Error:", ip, e)
        return None
    else:
        hostname = net_connect.find_prompt().replace(' ', '').replace(
            "#", '').replace('>', '').replace('(', '').replace(')', '')

        result.append(net_connect.send_config_set(
            cmdlist,
            delay_factor=delay_factor,
            max_loops=max_loops))
        # close the connection
        net_connect.disconnect()
        #
        result.append("\n")
        outputfile = '{}/{}_{}.txt'.format(outputdir, hostname, ip)

        if result:
            with open(outputfile, 'w') as out:
                for x in result:
                    out.write(x)
                out.write('\n')


# Provide switches to control this script
parser = argparse.ArgumentParser(
    # usage="%(prog)s [options] ; Use -h to show all options.",
    add_help=True,
    description='''This program is used to send one or more configuration
commands to IP addresses. The output is saved into separate files in a single
directory.''',
    epilog="Bash environment variables used: ACSUSER, ACSPASS")
parser.add_argument('-i', '--ip', required=True, help='''Input should
        be an IP address, a file containing IP addresses or an HPov
        csv export file.''')
parser.add_argument('--delay', required=False, type=float, default=1.5,
                    help='''Provide an alternative delay factor.
                            Default is %(default)s.''')
parser.add_argument('--processes', required=False, type=int, default=30,
                    help='''Provide an alternative amount of processes.
                            Default is %(default)s.''')
parser.add_argument('--maxloops', required=False, type=int, default=150,
                    help='''Provide the max loops, default is %(default)s.''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
# Multual exclusive group Only one of the following can be selected.
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-c', '--cmd', default=None, action='append',
                   help='Provide a single command between quotes.')
group.add_argument('-cf', '--cmdfile', default=None,
                   help='The path to the command file.')
args = parser.parse_args()

# Setting global variables
q = Queue()
threads = list()
lock = threading.Lock()
currenttime = time.strftime("%Y%m%d_%H%M%S")
# use the environment variable from bash
acsuser = lb.envvariable("ACSUSER", args.acsprefix)
acspass = lb.envvariable("ACSPASS", args.acsprefix)
acsenable = lb.envvariable("ACSENABLE", args.acsprefix)
outputdir = os.getenv("HOME")+"/working"
processes = args.processes
delay_factor = args.delay
max_loops = args.maxloops

# Staring an x amount of threads
for x in range(processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

# Doing some time calculation
start = time.time()

if args.cmdfile:
    if not os.path.isfile(args.cmdfile):
        sys.exit("The commands file doesn't exist. Exiting")
    else:
        with open(args.cmdfile, 'r') as f:
            cmdlist = [line for line in f]
elif args.cmd:
    cmdlist = args.cmd
else:
    sys.exit('No command(s) provided. Exiting')

# create dir if needed
if not os.path.isdir(outputdir):
    os.mkdir(outputdir)

# receive a list from the library. input can be an ip, iplist or hpov csv
ipfile, iperror = lb.readipfile(args.ip)

# which commands do you want to send?
print('These commands will be executed:')
for x in cmdlist:
    print(' ', x)

cont = input("Do you want to continue? yes/no? ")
if cont.lower() == 'yes':
    outputdir = outputdir + "/" + currenttime + "_executed" + "/"
    if not os.path.isdir(outputdir):
        os.mkdir(outputdir)
    for ip in ipfile:
        q.put(ip)
else:
    sys.exit("\n  Backing out...")

# wait until the thread terminates
q.join()

# stop workers
for i in range(processes):
    q.put(None)
for t in threads:
    t.join()

# end time - start time
print("\nTotal time to configure the devices:", time.time() - start)
print("The output is saved in:")
print("    ", outputdir)

if iperror:
    print("\n\nThe following lines from the source were not used because of \
errors:\n")
    for x in iperror:
        print(x)
