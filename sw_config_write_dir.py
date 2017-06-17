#!/usr/bin/env python3

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
    '''Configfile is expected to look like <hostname>_<ip>_<config.txt>'''
    ip = configfile.split('_')[1]
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    result = []

    device = {
        'device_type': 'cisco_ios',
        'ip': ip,
        'username': acsuser,
        'password': acspass,
        'secret': acsenable,
        'verbose': False,
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
        result.append(net_connect.enable())
        # automatically enters the config mode
        result.append(net_connect.send_command(
                      "wr mem",
                      strip_prompt=False,
                      strip_command=False))
        result.append("\n")
        # close the connection
        net_connect.disconnect()
        #
        outputfile = outputdir + "/" + configfile
        if result:
            with open(outputfile, 'w') as out:
                for x in result:
                    out.write(x)
                out.write('\n')


# Setting global variables
q = Queue()
threads = list()
lock = threading.Lock()
# outputdir = os.getenv("HOME")+"/working/"
currenttime = time.strftime("%Y%m%d_%H%M%S")
# use the environment variable from bash
acsuser = lb.envvariable("ACSUSER")
acspass = lb.envvariable("ACSPASS")
acsenable = lb.envvariable("ACSENABLE")
processes = 30
searchstring = "*config.txt"

try:
    inputdir = sys.argv[1]
except IndexError:
    print("one of the arguments isn't provided. Use the script like this:")
    sys.exit("script.py inputdir")

# Staring an x amount of threads
for x in range(processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

# Doing some time calculation
start = time.time()

# Putting the configuration files to the queue
print("These are the files you want to execute a 'wr mem':")

# files = (glob.glob1(inputdir, searchstring))
files = [fn for fn in glob.glob1(inputdir, searchstring)
         if not os.path.basename(fn).startswith('failed_')]
for file in files:
    print(file)

cont = input("Do you want to continue? yes/no? ")
if cont.lower() == 'yes':
    outputdir = inputdir + "/" + currenttime + "_wrmem" + "/"
    if not os.path.isdir(outputdir):
        os.mkdir(outputdir)
    for file in files:
        q.put(file)
else:
    sys.exit("Backing out...")

# wait until the thread terminates
q.join()

# stop workers
for i in range(processes):
    q.put(None)
for t in threads:
    t.join()

# end time - start time
print("\nTotal time to do a 'wr mem' on the devices:", time.time() - start)
print("The output is saved in:")
print("    ", outputdir)
