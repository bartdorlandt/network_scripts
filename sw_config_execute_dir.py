#!/usr/bin/env python3

import argparse
import glob
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


def execute(configfile):
    # Configfile is expected to look like <hostname>_<ip>_<config.txt>
    ip = configfile.split('_')[1]
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    result = []
    inputfile = inputdir + "/" + configfile

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
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        print("Error:", ip, e)
        return
        # result.append("Error: ")
        # result.append(str(e))
        # print ("result: ", result)
        # outputfile = outputdir + "/" + "failed_" + configfile
    else:
        result.append(net_connect.enable())
        #
        with open(inputfile, 'r') as f:
            for lists in lb.conf_range_gen(f.readlines(), 50, debug=debug):
                if debug:
                    print('lists:', lists)
                try:
                    result.append(net_connect.send_config_set(
                        config_commands=lists,
                        max_loops=max_loops,
                        delay_factor=delay_factor,
                        exit_config_mode=False))
                except ValueError as err:
                    print('ValueError received on:', ip)
                    print('error:', err)
                    print('verify manually where to continue.')
                else:
                    result.append("\n")
                    # Create the output file and put the results in it.
                    outputfile = outputdir + "/" + configfile
                    with open(outputfile, 'w') as out:
                        for x in result:
                            out.write(x)
                        out.write("\n")
                    net_connect.send_config_set(
                        config_commands=['\n'],
                        max_loops=max_loops,
                        delay_factor=delay_factor,
                        exit_config_mode=True)
        # close the connection
        net_connect.disconnect()

# Provide switches to control this script
parser = argparse.ArgumentParser(
    # usage="%(prog)s [options] ; Use -h to show all options.",
    add_help=True,
    description='''This program can be used to configure multiple devices
based on the configuration files in a directory. The output is saved into
a sub directory.''',
    epilog="Bash environment variables used: ACSUSER, ACSPASS")
parser.add_argument('--dir', required=True, help='''Input should
        be an IP address, a file containing IP addresses or an HPov
        csv export file.''')
parser.add_argument('-ss', '--searchstring', required=False,
                    default='*config.txt', help='''A search
        query for the file name. By default it searches for "*config.txt".''')
parser.add_argument('--delay', required=False, type=float, default=1.0,
                    help='''Provide an alternative delay factor.
                            Default is %(default)s.''')
parser.add_argument('--maxloops', required=False, type=int, default=150,
                    help='''Provide the max loops, default is %(default)s.''')
parser.add_argument('--processes', required=False, type=int, default=30,
                    help='''Provide an alternative amount of processes.
                            Default is %(default)s.''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
parser.add_argument('--debug', required=False, default=False,
                    action='store_true',
                    help='''enables debug functionality.''')
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
processes = args.processes
searchstring = "*config.txt"
delay_factor = args.delay
max_loops = args.maxloops
debug = args.debug
inputdir = args.dir

# Doing some time calculation
start = time.time()

# Putting the configuration files to the queue
print("These are the files you want to configure")

files = (glob.glob1(inputdir, searchstring))
print("\nThe amount of files: {}\n".format(len(files)))
for file in files:
    print(file)

cont = input("Do you want to continue? yes/no? ")
if cont.lower() == 'yes':
    outputdir = inputdir + "/" + currenttime + "_executed" + "/"
    if not os.path.isdir(outputdir):
        os.mkdir(outputdir)
    # Staring an x amount of threads
    for x in range(processes):
        # calling the function threader
        t = threading.Thread(target=threader)
        t.start()
        threads.append(t)

    for file in files:
        q.put(file)
        print('Reading file:', file)
else:
    sys.exit("\n  Backing out...")

# wait until the thread terminates
q.join()
if debug:
    print('q joined')

# stop workers
for i in range(processes):
    q.put(None)
for t in threads:
    t.join()

# end time - start time
print("\nTotal time to configure the devices:", time.time() - start)
print("The output is saved in:")
print("    ", outputdir)
