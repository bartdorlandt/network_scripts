#!/usr/bin/env python3

# v0.7 updated to match netmiko 1.1.0. Default delay increased.
# v0.6
# not creating directory if all is compliant.
# Not printing directory information if all is compliant.
# v0.5
# introducing non-intrusive option and argparse
# v0.4
# Using libbart for reading the ipfile or ip address.
# Added output to show the amount of files done.
# v0.3
# delay_factor needs to be set high enough to be wait for the answer for slow
# devices. (0.5 seems to do for an older stack of 4).
# FF v0.2 : IPv4!!
import argparse
import glob
import os
import threading
import time
import zipfile
from queue import Queue

from netmiko import ConnectHandler
from netmiko.ssh_exception import (NetMikoTimeoutException,
                                   NetMikoAuthenticationException)
from paramiko.ssh_exception import NoValidConnectionsError

from mylib import compliant as compli
from mylib import libbart as lb


# import sys
# import re
# from ciscoconfparse import CiscoConfParse


def threader():
    while True:
        # Getting the ip address out of the queue
        worker = q.get()
        if worker is None:
            break
        # print("Worker is: ", worker)
        # starting the other function which does the work
        compliant(worker, delay)
        # print("Compliant is: ", compliant)
        # completed with the job
        q.task_done()


# function to connect to the devices, do a sh run and run CiscoConfParse on it.
def compliant(ip, delay):
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    device = {
        'device_type': devicetype,
        'ip': ip,
        'username': acsuser,
        'password': acspass,
        'secret': acsenable,
        'verbose': False,
        'global_delay_factor': delay,
    }

    # result is used to save the configuration
    result = []
    # error is used to save the errors
    error = []

    try:
        # Opening the connection via ssh
        net_connect = ConnectHandler(**device)
        hostname = net_connect.find_prompt().strip("#")
        # output = net_connect.send_config_from_file(config_file=cmdfile)
        # net_connect.send_command(' ')
        result.append(net_connect.enable())
        result.append(net_connect.send_command('sh run'))
        # close the connection
        net_connect.disconnect()
        try:
            sw = lb.Switch(ip, acsprefix=acsprefix, delay_factor=delay)
        except ConnectionError as err:
            print('SNMP error:', ip, err)
            return
        try:
            switchtype = sw.getdevicetype()['sw1']
        except KeyError:
            print('Error getting info for this ip:', ip)
            print('Probably a modular switch.')
            return
        # using the library to do the checks on the orignal result, which is
        # splitted on newlines. A ciscoconfparsed list is returned.
        # print("starting with the lib", ip)
        with lock:
            # print('intrusive = {}'.format(intrusive))
            cfgdiffs, error = compli.all(result[0].split('\n'),
                                         sw1=switchtype,
                                         ip=ip,
                                         hostname=hostname,
                                         intrusive=intrusive)
        #
        if cfgdiffs.ioscfg:
            if not os.path.isdir(outputdir):
                os.mkdir(outputdir)
            # output file
            outputfile = outputdir + hostname + "_" + ip + "_config.txt"
            # writing the file
            cfgdiffs.save_as(outputfile)
            #
            # If a zip file is created, at these files to the zip file
            if createzip:
                zipf = zipfile.ZipFile('{}output.zip'.format(outputdir), 'a')
                zipf.write(outputfile)
                zipf.close()
        else:
            print('\t*** This device is compliant:', ip)

    except NetMikoTimeoutException as e:
        print("Device timeout. IP:", ip)
        # print("error:", e)
        hostname = "timeout"
        # print("result: ", result)
        # error.append("Error: NetMikoTimeoutException")
        error.append(
            "Error: NetMikoTimeoutException. IP: {}, {}\n".format(ip, str(e)))
        # error.append(ip)
        # error.append(str(e))
        # error.append("\n")

    except NetMikoAuthenticationException as e:
        print("Authentication isn't working at this moment. IP:", ip)
        hostname = "auth.issue"
        # error.append("Error: NetMikoAuthenticationException")
        error.append(
            "Error: NetMikoAuthenticationException. IP: {}, {}\n".format(
                ip, str(e)))
        # error.append(ip)
        # error.append(str(e))
        # error.append("\n")

    except NoValidConnectionsError as e:
        print("Not able to set up a connection via ssh. IP:", ip)
        hostname = "ssh.issue"
        error.append(
            "Error: NoValidConnectionsError. IP: {}, {}\n".format(
                ip, str(e)))
        # error.append(ip)
        # error.append(str(e))
        # error.append("\n")

    if error:
        with lock:
            if not os.path.isdir(outputdir):
                os.mkdir(outputdir)
            errorfilename = outputdir + "errors.txt"
            errorfile = open(errorfilename, 'a')
            for x in error:
                errorfile.write(x)
            errorfile.write("\n")
            errorfile.close()

# Argparse with options.
parser = argparse.ArgumentParser(
    add_help=True,
    description='''This program is used to verify baseline compliancy for the IT
environment. Anything that isn't compliant is saved in text files which can
be used to update the existing configuration. In case an error occurs and you
think the device is working, try increasing the delay.''',
    epilog="Bash environment variables used: ACSUSER, ACSPASS")
parser.add_argument('-i', '--ip', required=True, help='''Input should be an
IP address, a file containing IP addresses or an HPov csv export file.''')
parser.add_argument('--intrusive', action='store_const', const='yes',
                    help='''Do you want to include intrusive commands.''',
                    required=False)
parser.add_argument('-g', '--genipfile', action='store_const', const='yes',
                    help='''Do you wish to generate an ipfile in
                    the output direcotry?''', required=False)
parser.add_argument('-z', '--zipfile', action='store_const', const='yes',
                    help='''Do you wish to generate a zipfile in
                    the output direcotry?''', required=False)
parser.add_argument('--delay', required=False, type=float, default=1.0,
                    help='''Provide an alternative delay factor.
                    Default is %(default)s.''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
parser.add_argument('--telnet', default=None, required=False,
                    action='store_true', help='''Use telnet instead of SSH.''')
args = parser.parse_args()

# Setting global variables
sitename = None
devicedict = {}
q = Queue()
threads = list()
delay = args.delay
acsprefix = args.acsprefix
devicetype = 'cisco_ios'
lock = threading.Lock()
currenttime = time.strftime("%Y%m%d_%H%M%S")
# use the environment variable from bash
acsuser = lb.envvariable("ACSUSER", acsprefix)
acspass = lb.envvariable("ACSPASS", acsprefix)
acsenable = lb.envvariable("ACSENABLE", acsprefix)
processes = 30
# ipre = re.compile('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
iplist = []
inputtype = None
searchstring = "*config.txt"
input1 = args.ip
intrusive = None
genipfile = None
createzip = None
if args.intrusive:
    intrusive = args.intrusive
if args.genipfile:
    genipfile = args.genipfile
if args.zipfile:
    createzip = args.zipfile
if args.telnet:
    devicetype = 'cisco_ios_telnet'

# Filling the dict with the IP addresses
# print("start reading the input")
iplist, iperror = lb.readipfile(input1)

# print("input1: ", input1)
# print("iplist: ", iplist)

if len(iplist) == 1:
    workdir = os.path.expanduser('~') + '/working'
else:
    workdir = os.path.dirname(os.path.realpath(input1))

outputdir = workdir + "/" + currenttime + "_compliant" + "/"


# Staring an x amount of threads
for x in range(processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

# Doing some time calculation
# start = time.time()

# print("done with the input. It took:", time.time() - start )
print("Total IPs:", len(iplist))
if iperror:
    print("Total errors:", len(iperror))
    print('''\n\nThe following lines from the source were not used because of
errors:\n''')
    for x in iperror:
        print(x)

# Doing some time calculation
start = time.time()

# print("temp: iplist: ", iplist)
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

# Only if the option genipfile is given
if genipfile:
    if not os.path.isdir(outputdir):
        os.mkdir(outputdir)
    with open(outputdir + "ipfile", 'a') as f:
        for ip in iplist:
            f.write("{}\n".format(ip))

files = (glob.glob1(outputdir, searchstring))

# end time - start time
print("\nTotal time after input:", time.time() - start)
if not len(files) == 0:
    print("Total output files: {}. The output is saved in:".format(len(files)))
    print("    ", outputdir)
