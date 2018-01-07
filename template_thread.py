#!/usr/bin/env python3
'''
Template for multithreading
'''
import argparse
import threading
import time
from queue import Queue
# from collections import deque, Counter

from mylib import libbart as lb


def threader():
    while True:
        # Getting the ip address out of the queue
        worker = q.get()
        if worker is None:
            break
        # starting the other function which does the work
        multithreaded(worker)
        # completed with the job
        q.task_done()


def multithreaded(ip):
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    pass


# Provide switches to control this script
parser = argparse.ArgumentParser(
    add_help=True,
    description='''With this script you can gather information of the switches
per switch per port an overview of the vlan, the mac address(es) and ip
address. The output is saved in a separate file in a single directory.
''',
    epilog="Environment variables used: ACSUSER, ACSPASS, CISCOCOMMUNITY")

parser.add_argument('-i', '--ip', required=True, help='''Input should
        be an IP address, a file containing IP addresses or an HPov
        csv export file.''')
parser.add_argument('--delay', required=False, type=float, default=1.0,
                    help='''Provide an alternative delay factor.
                            Default is %(default)s.''')
parser.add_argument('--processes', required=False, type=int, default=30,
                    help='''Provide an alternative amount of processes.
                            Default is %(default)s.''')
parser.add_argument('-sc', required=True,
                    help='''Provide the site code.''')
args = parser.parse_args()

# use the environment variables
delay = args.delay
outputdir = os.getenv("HOME")+"/working/"
q = Queue()
threads = list()
# lock = threading.Lock()

# Creating the sub-directory to save the files
currenttime = time.strftime("%Y%m%d_%H%M%S")+"_"+args.sc+"_template/"
if not os.path.isdir(outputdir):
    os.mkdir(outputdir+currenttime)

# Staring an x amount of threads
for x in range(args.processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

# Doing some time calculation
# start = time.time()

# receive a list from the library. input can be an ip, iplist or hpov csv
iplist, iperror = lb.readipfile(args.ip)

# Running through the IP addresses
for ip in iplist:
    # Putting the ip in the queue
    # print ("putting the", ip, "to the queue")
    q.put(ip)

# wait until the thread terminates
q.join()

# stop workers
for i in range(args.processes):
    q.put(None)
for t in threads:
    t.join()

# Print an error for IP's that couldn't be processed.
if iperror:
    print("\n\nThe following lines from the source were not used because of \
errors:\n")
    for x in iperror:
        print(x)
