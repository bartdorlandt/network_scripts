#!/usr/bin/env python3
'''
It is used to send commands to devices. These devices can be,
cisco_wlc, cisco_ios_telnet, cisco_ios, cisco_asa; the default is cisco_ios.

There are some preconfigured command lists, like premigration and status. These
will give sufficient output to get information from the devices. These are
specifically used for switches.

Output is generated as a file per IP basis inside the working directory.
'''
# Information: https://pynet.twb-tech.com/blog/automation/netmiko.html
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


def verifypath(path, exist=True):
    if exist:
        return os.path.isfile(path)
    else:
        return not os.path.isfile(path)


def device_connect(ip, delay):
    # global failedcount
    result = []
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    #
    device = {
        'device_type': devicetype,
        'ip': ip,
        'username': acsuser,
        'password': acspass,
        'secret': acsenable,
        'verbose': False,
        'global_delay_factor': delay,
    }
    #
    try:
        # Opening the connection via ssh
        net_connect = ConnectHandler(**device)
    except NetMikoTimeoutException as e:
        print("Timeout Error:", ip, e)
        return None
    except NetMikoAuthenticationException as e:
        print("Authentication Error:", ip, e)
        return None
    except ValueError as e:
        print("Value Error:", ip, e)
        return None
    else:
        net_connect.enable()
        hostname = net_connect.find_prompt().replace(' ', '').replace(
            "#", '').replace('>', '').replace('(', '').replace(
            ')', '').replace('/', '_')
        # Send the contents of the cmdfile to the cisco device
        for line in cmdlist:
            # imitating the command prompt, since it normally isn't printed
            # commandline = hostname+"#"+line
            # result.append(commandline)
            try:
                result.append(net_connect.send_command(
                    line, strip_prompt=False, strip_command=False))
            except OSError as err:
                print("Something went wrong: OSError:", err, 'on IP:', ip)
                pass
            # result.append(net_connect.send_command('!'))
            result.append("\n!\n")
        #
        # Disconnect the session
        net_connect.disconnect()
        #
        filename = outputdir+currenttime+hostname+"_"+ip+".txt"
        with open(filename, 'w') as outputfile:
            for x in result:
                outputfile.write(x)
            outputfile.write("\n")


def threader():
    while True:
        # Getting the ip address out of the queue
        worker = q.get()
        if worker is None:
            break
        # starting the other function which does the work
        device_connect(worker, delay)
        # completed with the job
        q.task_done()

# Provide switches to control this script
parser = argparse.ArgumentParser(
    # usage="%(prog)s [options] ; Use -h to show all options.",
    add_help=True,
    description='''This program is used to send one or more commands to
IP addresses. The output is saved into separate files in a single directory.
Additional features are able to be set, like premigration or status to quickly
generate information for the switch(es).
''',
    epilog="Bash environment variables used: ACSUSER, ACSPASS, ACSENABLE")

parser.add_argument('-i', '--ip', required=True, help='''Input should
        be an IP address, a file containing IP addresses or an HPov
        csv export file.''')
parser.add_argument('-d', '--devicetype', default='cisco_ios', required=False,
                    help='''Provide the device type: cisco_wlc, cisco_asa,
                    cisco_ios, cisco_ios_telnet;  Default is %(default)s''')
parser.add_argument('--delay', required=False, type=float, default=1.0,
                    help='''Provide an alternative delay factor.
                            Default is %(default)s.''')
parser.add_argument('--processes', required=False, type=int, default=30,
                    help='''Provide an alternative amount of processes.
                            Default is %(default)s.''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
# Multual exclusive group Only one of the following can be selected.
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-c', '--cmd', default=None, action='append',
                   help='Provide a single command between quotes.')
group.add_argument('-cf', '--cmdfile', default=None,
                   help='The path to the command file.')
group.add_argument('-pm', '--premigration', default=None, action='store_true',
                   help='If set the premigration commands are executed.')
group.add_argument('-sist', '--shintstatus', default=None, action='store_true',
                   help='If set, sh int status command is executed.')
group.add_argument('-st', '--status', default=None, action='store_true',
                   help='If set the status commands are executed.')
args = parser.parse_args()

# ipcount = 0
# failedcount = 0
delay = args.delay
# use the environment variable from bash
acsuser = lb.envvariable("ACSUSER", args.acsprefix)
acspass = lb.envvariable("ACSPASS", args.acsprefix)
acsenable = lb.envvariable("ACSENABLE", args.acsprefix)
devicetype = args.devicetype

outputdir = os.getenv("HOME")+"/working/"
q = Queue()
threads = list()
lock = threading.Lock()

# #######################################################
# Check this function, can it be clearer?
#####################
# if verifypath(args.ip, False):
#    sys.exit("The ip file doesn't exist. Exiting")

if args.cmdfile:
    if verifypath(args.cmdfile, False):
        sys.exit("The commands file doesn't exist. Exiting")
    else:
        cmdlist = []
        with open(args.cmdfile, 'r') as f:
            for line in f:
                cmdlist.append(line)
elif args.cmd:
    # cmdlist = cmd.split('\n')
    cmdlist = args.cmd
elif args.premigration:
    cmdlist = ['sh run', 'sh ip int brief', 'sh int status',
               'sh spanning-tree root', 'sh int trunk', 'sh vtp status',
               'sh vtp password', 'sh int description', 'sh vlan brief',
               'sh ip route connected', 'sh ip route static',
               'sh cdp nei detail', 'sh etherchannel sum', 'sh inventory',
               'sh module', 'sh version', 'sh mac addr', 'sh cdp nei']
elif args.shintstatus:
    cmdlist = ['sh int status']
elif args.status:
    cmdlist = ['sh int status', 'sh int description', 'sh ip int brief',
               'sh vlan brief', 'sh spanning-tree root',
               'sh ip route connected',
               'sh ip route static', 'sh cdp nei detail', 'sh int trunk',
               'sh vtp status', 'sh vtp password', 'sh cdp nei detail',
               'sh etherchannel sum', 'sh inventory', 'sh module',
               'sh version']
else:
    sys.exit('No command(s) provided. Exiting')

# create dir if needed
if not os.path.isdir(outputdir):
    os.mkdir(outputdir)

# Creating the sub-directory to save the files
if args.premigration:
    currenttime = time.strftime("%Y%m%d_%H%M%S")+"_premigration/"
elif args.shintstatus:
    currenttime = time.strftime("%Y%m%d_%H%M%S")+"_shintstatus/"
elif args.status:
    currenttime = time.strftime("%Y%m%d_%H%M%S")+"_status/"
else:
    currenttime = time.strftime("%Y%m%d_%H%M%S")+"_cmd/"
os.mkdir(outputdir+currenttime)

# Staring an x amount of threads
for x in range(args.processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

# Doing some time calculation
start = time.time()

# receive a list from the library. input can be an ip, iplist or hpov csv
ipfile, iperror = lb.readipfile(args.ip)

# Running through the IP addresses
for ip in ipfile:
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

# end time - start time
print("\nTotal time:", time.time() - start)
# print("Total devices done:", str(ipcount))
# if failedcount:
#     print("\tamount failed:", str(failedcount) + "\n")
print("The output is saved in:")
print("  ", outputdir+currenttime)

if iperror:
    print("\n\nThe following lines from the source were not used because of \
errors:\n")
    for x in iperror:
        print(x)
