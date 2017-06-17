#!/usr/bin/env python3
'''This program is used to provide information on what the current status
is of switchports and when it was last changed. This information can be
provided using text files with ;-separated fields (default) or it can
provide an excel file.

Bash environment variables used:
- CISCOCOMMUNITY
'''
import argparse
import datetime
import os
import sys
import time
import threading
from queue import Queue

import xlsxwriter
from hnmp import SNMP

from mylib import libbart as lb


def threader():
    while True:
        # Getting the ip address out of the queue
        worker = q.get()
        if worker is None:
            break
        # starting the other function which does the work
        dictuptime(worker)
        # completed with the job
        q.task_done()


def dictuptime(ip):
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    global dupt
    try:
        dupt[ip] = lb.uptime(ip, device=devicetype, acsprefix=acsprefix)
    except IndexError as err:
        print("Couldn't get the uptime for ip:", ip, "Error:", err)
        dupt[ip] = ''


def split_ip(ip):
    return tuple(int(part) for part in ip.split('.'))


# Module createexcel
def createexcel(site, hostname, ip, outputdir, topinfo, headerlist,
                headerwidth, deviceinfo, count, totalip, reddays,
                workbook=None):
    # index = 1
    row = 0
    col = 0
    headertotal = len(headerlist.split(';'))-1
    today = datetime.date.today().strftime("%Y%m%d")

    if not workbook:
        # Only create a workbook on the first creation
        if totalip == 1:
            workbook = xlsxwriter.Workbook(
                '{}/{}_{}_{}_{}.xlsx'.format(outputdir, today, site,
                                             hostname, ip))
        else:
            workbook = xlsxwriter.Workbook('{}/{}_{}.xlsx'.format(
                outputdir, today, site))

    worksheet = workbook.add_worksheet('_'.join((hostname, ip)))

    header = workbook.add_format()
    header.set_bold()
    red = workbook.add_format()
    red.set_color("red")
    for x in headerwidth:
        worksheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), x)
        col += 1
    worksheet.set_default_row(16)
    col = 0
    for x in topinfo.split('\n'):
        worksheet.write(row, col, x)
        row += 1

    beginrow = row
    tableheader = []
    for x in headerlist.split(';'):
        worksheet.write(row, col, x, header)
        tableheader.append({'header': x})
        col += 1

    row += 1
    col = 0
    for x in deviceinfo:
        IF, VLAN, ADMIN, OPER, DAYS = x.split(';')
        worksheet.write(row, col, IF)
        worksheet.write(row, col + 1, VLAN)
        worksheet.write(row, col + 2, ADMIN)
        worksheet.write(row, col + 3, OPER)
        if ((int(DAYS.split()[0]) > reddays) and
                (ADMIN == 'enabled') and
                (OPER == 'down')):
            worksheet.write(row, col + 4, DAYS, red)
            # print (DAYS)
        else:
            worksheet.write(row, col + 4, DAYS)
        row += 1

    # making a table, with header
    worksheet.add_table(beginrow, 0, row-1, headertotal,
                        {'columns': tableheader})
    # table_name = table.name

    if count == totalip - 1:
        workbook.close()

    return workbook


# Useful information:
# MIBs used:
# http://www.oidview.com/mibs/0/IF-MIB.html
# http://www.oidview.com/mibs/9/CISCO-VLAN-MEMBERSHIP-MIB.html


# Provide switches to control this script
parser = argparse.ArgumentParser(
    add_help=True,
    description='''This program is used to provide information on what the
    current status is of switchports and when it was last changed. This
    information can be provided using text files with ;-separated fields
    (default) or it can provide an excel file.''',
    epilog="Bash environment variables used: CISCOCOMMUNITY")
parser.add_argument('-i', '--ip', required=True, help="Input should \
be an IP address, a file containing IP addresses or an HPov csv export \
file.")
parser.add_argument('-e', '--excel', action='store_const', const='yes',
                    default=None,
                    required=False,
                    help='''Enable this if you want to create
                    an excel file instead''')
parser.add_argument('-r', '--red', type=int,
                    default=60, required=False,
                    help='''The provided number is used for marking the
                    amount of days higher than this number.
                    Default is %(default)s. If no marking is desired,
                    use 0''')
parser.add_argument('--processes', required=False, type=int, default=30,
                    help='''Provide an alternative amount of processes.
                    Default is %(default)s.''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
parser.add_argument('--telnet', default=None, required=False,
                    action='store_true', help='''Use telnet instead of SSH.''')
args = parser.parse_args()

arg1 = args.ip
reddays = args.red
excel = args.excel
workbook = None
sitename = None
acsprefix = args.acsprefix
devicetype = 'cisco_ios'
processes = args.processes
communitystring = lb.envvariable("CISCOCOMMUNITY", acsprefix)
ipfile, iperror = lb.readipfile(arg1)
today = datetime.date.today().strftime("%Y%m%d")
q = Queue()
threads = list()
lock = threading.Lock()
dupt = dict()
if args.telnet:
    devicetype = 'cisco_ios_telnet'
if args.red == 0:
    reddays = 100000000

# Start the clock
start = time.time()

if ipfile:
    totalip = len(ipfile)
    workdir = os.path.expanduser('~') + '/working'
    currenttime = time.strftime("%Y%m%d_%H%M%S")
    outputdir = workdir + "/" + currenttime + "_portstate" + "/"
    if not os.path.isdir(outputdir):
        os.mkdir(outputdir)
else:
    sys.exit("No valid IPs.")

# Staring an x amount of threads
for x in range(processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

# print('Before q.put.')
# print(time.time() - start)

# Filling the queue
for ip in ipfile:
    # Putting the ip in the queue
    # print ("putting the", ip, "to the queue")
    q.put(ip)

# wait until the thread terminates
q.join()

# stop workers
for i in range(processes):
    q.put(None)
for t in threads:
    t.join()

print('Done with the multithreaded part.')
# print(time.time() - start)

for count, ip in enumerate(sorted(ipfile, key=lb.split_ip)):
    # print('Per IP: ' + ip)
    # print(time.time() - start)
    output = []
    snmp = SNMP(ip, community=communitystring)
    # uptime = snmp.get("1.3.6.1.2.1.1.3.0")
    # Using the uptime via a sh ver, more reliable.
    fqdn = snmp.get("1.3.6.1.2.1.1.5.0")
    snmplocation = snmp.get("1.3.6.1.2.1.1.6.0")
    # print("uptime:", uptime, "\nfqdn:", fqdn, "\nLocation:", snmplocation)
    # IF description
    # http://www.oidview.com/mibs/0/IF-MIB.html , ifEntry
    mib = '1.3.6.1.2.1.2.2.1'
    # mib = "1.3.6.1.4.1.14179.2.1.4.1"
    port_info = snmp.table(
        mib,
        columns={
            1: "ifIndex",
            2: "ifDescr",
            7: "ifAdminStatus",
            8: "ifOperStatus",
            9: "ifLastChange",
        },
        column_value_mapping={
            "ifAdminStatus": {
                1: "enabled",
                2: "shutdown",
            },
            "ifOperStatus": {
                1: "up",
                2: "down",
            },
        },
        fetch_all_columns=False,
    )

    # vlan info
    # http://www.oidview.com/mibs/9/CISCO-VLAN-MEMBERSHIP-MIB.html
#    mib = '1.3.6.1.4.1.9.9.68.1.2.2.1'
#    vlan_info = snmp.table(
#        mib,
#        columns={
#            2: "vmVlan",
#        },
#        column_value_mapping={
#        },
#        fetch_all_columns=False,
#    )
#
    hostname = fqdn.split('.')[0]
    #
    for x, intf in enumerate(port_info.columns['ifDescr']):
        if "thernet" in intf and "ontrolled" not in intf:
            # Get the position of this entry in the list
            intfloc = port_info.columns['ifDescr'].index(intf)
            # Get the ifindex with that entry number
            ifindex = str(port_info.columns['ifIndex'][intfloc])
            # Get the vlan number belonging to the ifindex as a string.
            vlannum = str(snmp.get('1.3.6.1.4.1.9.9.68.1.2.2.1.2.' + ifindex))

            if dupt[ip] == '':
                uptime_output = "couldn't get it."
            else:
                uptime_output = (
                    str((dupt[ip] - port_info.columns[
                        'ifLastChange'][x]).days) + " days ago")
            text = port_info.columns['ifDescr'][x] + ';' + \
                vlannum + ';' + \
                port_info.columns['ifAdminStatus'][x] + ';' + \
                port_info.columns['ifOperStatus'][x] + ';' + \
                uptime_output
            output.append(text)
    #
    topinfo = 'Hostname: {}, IP: {}\nLocation: {}\nUptime: {}\
\nHighlighted above {} days\n\n'.format(
        hostname, ip, snmplocation, str(dupt[ip]).split('.')[0], str(reddays))
    header = 'Interface;Vlan;IF admin state;IF operational state;Last state \
change'
    if excel:
        headerwidth = [26, 10, 20, 20, 20]
        if not sitename:
            try:
                sitename = snmplocation.split(',')[0]
            except:
                sitename = 'put_manually'
        workbook = createexcel(sitename, hostname, ip, outputdir,
                               topinfo, header, headerwidth, output, count,
                               totalip, reddays, workbook)
    else:
        with open(
                outputdir + today + '_' + hostname + '_' + ip + '.txt', 'a') \
                    as f:
            f.write(topinfo)
            f.write(header)
            f.write('\n')
            for x in output:
                f.write(x)
                IF, VLAN, ADMIN, OPER, DAYS = x.split(';')
                if ((int(DAYS.split()[0]) > reddays) and
                        (ADMIN == 'enabled') and
                        (OPER == 'down')):
                    f.write('    <== over the limit')
                f.write('\n')

print("\nTotal time: {}".format(time.time() - start))
print("Total devices done: {}".format(totalip))
print("The output is saved in:")
print("  ", outputdir)

if iperror:
    print("\n\nThe following lines from the source were not used because of \
    errors:\n")
    for x in iperror:
        print(x)

# Get the info
# port_info.columns['ifIndex']
# port_info.columns['ifDescr']
# port_info.columns['ifAdminStatus']
# port_info.columns['ifOperStatus']
# port_info.columns['ifLastChange']
