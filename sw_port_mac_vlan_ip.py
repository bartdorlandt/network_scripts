#!/usr/bin/env python3
'''
This script is used to gather information from the provided switches. This
includes a per port overview of the mac address(es), ip address, vlan.
But it will also show the MAC vendor if known.

Output is generated as an excel file.
'''
import argparse
import os
import re
import threading
import time
import sys
# import datetime
from queue import Queue
import requests
import xlsxwriter
from hnmp import SNMP

from mylib import libbart as lb


def threader():
    while True:
        # Getting the ip address out of the queue
        worker = q.get()
        if worker is None:
            break
        if args.debug:
            print('starting thread with ip:', worker)
        # starting the other function which does the work
        l2switch(worker)
        # completed with the job
        q.task_done()


def dictuptime(ip):
    """Getting the uptime in datetime value"""
    try:
        uptime = lb.uptime(ip, device=devicetype, acsprefix=acsprefix)
    except IndexError as err:
        print("Couldn't get the uptime for ip:", ip, "Error:", err)
        uptime = None
    return uptime


def porttimedict(ip, uptime):
    portdict = dict()
    mib = '1.3.6.1.2.1.2.2.1'
    snmp = SNMP(ip, community=communitystring)
    #
    try:
        snmplocation = snmp.get("1.3.6.1.2.1.1.6.0")
        port_info = snmp.table(
            mib,
            columns={
                # 1: "ifIndex",
                2: "ifDescr",
                9: "ifLastChange",
            },
            fetch_all_columns=False,
        )
    except hnmp.SNMPError as err:
        print("Couldn't get snmp information from ip:", ip, "Error:", err)
        return None, None
    except:
        print("Something went wrong:", ip, 'Error:', sys.exc_info()[0])
        return None, None
    #
    if not uptime:
        # part below only makes sense with a valid uptime.
        return snmplocation, None
    for x, intf in enumerate(port_info.columns['ifDescr']):
        if "thernet" in intf and "ontrolled" not in intf:
            shortintf = intf.replace(
                'nGigabitEthernet', '').replace(
                'gabitEthernet', '').replace('stEthernet', '')
            portdict[shortintf] = str(
                (uptime -
                    port_info.columns['ifLastChange'][x]).days) + " days ago"
    #
    return snmplocation, portdict


def l2switch(ip):
    print("Starting with ip: {:<16} thread name: {}".format(
        ip, threading.currentThread().getName()))
    global allswitchinfo
    #
    l2 = list()
    #
    # Get the hostname
    try:
        sw = lb.Switch(ip, acsprefix=acsprefix, delay_factor=delay)
        hostname = sw.gethostname()
    except ConnectionError as err:
        print("Couldn't get the hostname from this IP using snmp:", ip, err)
        hostname = ''
    #
    shmaccmd = 'sh mac addr | e Po|CPU|---|criterion'
    try:
        status = lb.getcmdoutput(ip, 'sh int status', delay_factor=delay,
                                 device=devicetype, acsprefix=acsprefix)
        # Get the mac addresses for the active ports.
        shmac = lb.getcmdoutput(ip, shmaccmd, delay_factor=delay,
                                device=devicetype, acsprefix=acsprefix)
        # also getting the description
        desc = lb.getcmdoutput(ip, 'sh int desc', delay_factor=delay,
                               device=devicetype, acsprefix=acsprefix)
    except:
        print('SSH session failed:', ip, "Error:", sys.exc_info()[0])
        return
    #
    # Get the uptime of the device.
    uptime = dictuptime(ip)
    # Get the port lastchange date information and the snmp location.
    snmplocation, portdict = porttimedict(ip, uptime)
    #
    descdict = {x.split()[0]: x[55:] for x in desc.split('\n')}
    # for x in descdict: print(x, '    ' ,descdict[x])
    #
    if not status or not shmac:
        print("Commands can't be executed on the switch. IP: {}".format(ip))
        return
    #
    for line in status.split('\n'):
        maclist = list()
        vmac = 'na'
        mac = 'na'
        if reINT.search(line):
            iface = line.split()[0]
            if ('No Transceiver' in line or
                    'Not Present' in line or
                    '1000BaseSX SFP' in line or
                    '1000BaseLX SFP' in line or
                    '10/100/1000BaseTX SFP' in line):
                ifstatus = line.split()[-6]
                vlan = line.split()[-5]
            else:
                ifstatus = line.split()[-5]
                vlan = line.split()[-4]
            #
            if ifstatus != 'connected' or vlan == 'trunk':
                l2.append('{};{};{};{};{};{};{}'.format(
                    iface, descdict[iface], vlan, ifstatus,
                    portdict[iface], mac, vmac))
                continue
            #
            for intf in shmac.split('\n'):
                # if '10' in intf:
                #     print(intf)
                # In case of 4500/6500 "sh mac addr", shortning the Interface.
                intf = intf.replace('GigabitEthernet', 'Gi')
                # Search for a mac address using RE, and match on the interface
                if reMAC.search(intf) and intf.split()[-1] == iface:
                    mac = reMAC.search(intf).group(1)
                    macvlan = intf.split()[0]
                    # print('mac', mac)
                    if macvlan in voicevlan:
                        vmac = mac
                        # print('vmac', vmac)
                    else:
                        # print('mac append', mac)
                        maclist.append(mac)
            #
                    if args.debug:
                        if iface == 'Gi1/0/3':
                            print('L2 debug: {}\nintf: {}\niface: {}, ifdesc: {}, \
vlan: {}, ifstatus: {}, lastchange: {}, mac: {}\nmacvlan: {}, vmac: {}\n\
maclist: {}'.format(ip, intf, iface, ifdesc[iface], vlan, ifstatus,
                                portdict[iface], mac, macvlan, vmac, maclist))
            #
            if maclist:
                # Using a # to join to make it consistent. # is not used in the
                # OUI datase.
                datamac = '#'.join(maclist)
            else:
                datamac = 'na'
            #
            if args.debug:
                if iface == 'Gi1/0/3':
                    print('L2 debug: datamac:', datamac)
            #
            # interface, IF description, vlan, IF status,
            #   Data mac addresses, Voice MAC addresses
            l2.append('{};{};{};{};{};{};{}'.format(
                iface, descdict[iface], vlan, ifstatus,
                portdict[iface], datamac, vmac))
            # if 'Gi1/0/10' in line:
            #     print('Gi1/0/10:', iface, vlan, ifstatus, datamac, vmac)
            #     print('l2:', l2)
    #
    allswitchinfo[ip] = [hostname, l2, snmplocation,
                         str(uptime).split('.')[0]]


def l3info(l3ip):
    '''function to get the arp table for all VRF's.
    It returns a dict with the MAC as the key and the IP address as the value.
    '''
    vrfset = set()
    vlbrdict = dict()
    arpdict = dict()
    reARP = re.compile('Internet +(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) .*? +'
                       '([0-9a-z]{4}\.[0-9a-z]{4}\.[0-9a-z]{4})')
    #
    vrfbr = lb.getcmdoutput(l3ip, 'sh ip vrf', delay_factor=delay,
                            device=devicetype, acsprefix=acsprefix)
    for x in vrfbr.split('\n'):
        if x and x.replace('  ', '', 1)[0].isalpha():
            if not (x.split()[0] == 'Name' or
                    x.split()[0] == 'Liin-vrf' or
                    x.split()[0] == 'mgmtVrf'):
                vrfset.add(x.split()[0])
    #
    cmd = 'sh ip arp\n'
    for vrf in vrfset:
        cmd = cmd + 'sh ip arp vrf ' + vrf + '\n'
    arplist = lb.getcmdoutput(l3ip, cmd, delay_factor=delay,
                              device=devicetype,
                              acsprefix=acsprefix).split('\n')
    #
    for x in arplist:
        match = reARP.search(x)
        if match:
            mac = match.group(2)
            ip = match.group(1)
            arpdict[mac] = ip
    #
    # ########## Getting a list of vlans
    vlbr = lb.getcmdoutput(l3ip, 'sh vlan br',
                           device=devicetype, acsprefix=acsprefix)
    #
    for x in vlbr.split('\n'):
        if x and x[0].isdigit():
            vlan = x.split()[0]
            if vlan in ('1002', '1003', '1004', '1005'):
                continue
            name = x[5:38].rstrip()
            if vlan and name:
                vlbrdict[vlan] = name
    #
    return arpdict, vlbrdict
    # ip = '10.205.200.254'
    # a = l3info(ip)
    # for x in a:
    #     print(x, a[x])


def maclookup(MAC):
    '''Doing a vendor lookup based on the MAC address. But first it'll try to
    find it in the mac dictionary, for previous searches to speed things up.
    If no entry is found it will do a lookup on the internet.
    '''
    global macdict
    mac = MAC.lower()
    #
    # First do a local lookup on the prefix instead of contacting the internet.
    first6 = mac.replace('.', '').replace(':', '')[0:6]
    try:
        return macdict[first6]
    except KeyError:
        pass
    #
    # If it doesn't exists, do an internet lookup.
    mac_url = 'http://macvendors.co/api/%s'
    r = requests.get(mac_url % mac)
    #
    # print('try company: {}'.format(r.json()['result']))
    try:
        company = r.json()['result']['company']
        # macprefix = r.json()['result']['mac_prefix']
        # address = r.json()['result']['address']
        # country = r.json()['result']['country']
        # starthex = r.json()['result']['start_hex']
    except:
        company = None
    #
    if company:
        macdict[first6] = company
        return company
    else:
        return 'No vendor found'


def maclookup2(MAC):
    '''Doing a vendor lookup based on the MAC address. It will use the global
    dict to retrieve the information.
    '''
    # start = time.time()
    first6 = MAC.upper().replace('.', '').replace(':', '')[0:6]
    try:
        return ouidict[first6]
    except KeyError:
        return 'No vendor found'


def combinel2arpvendor(arpdict):
    global allswitchinfo
    #
    # loop through all IP's
    for ip in allswitchinfo:
        macipvendor = list()
        hostname = allswitchinfo[ip][0]
        snmplocation = allswitchinfo[ip][2]
        uptime = allswitchinfo[ip][3]
        #
        # loop through each interface
        for line in allswitchinfo[ip][1]:
            # print('line:', line)
            maclist = list()
            maciplist = list()
            macvendorlist = list()
            vmacip = ''
            vmacvendor = ''
            # iface;vlan;ifstatus;mac;vmac)
            iface, ifdesc, vlan, ifstatus, lastchange, \
                macgroup, vmac = line.split(';')
            # print(iface, vlan, ifstatus, macgroup, vmac)
            if macgroup and macgroup != 'na':
                # organizing mac and IP addresses
                # Using a # to join to make it consistent. # is not used in the
                # OUI datase.
                for mac in macgroup.split('#'):
                    # print('mac:', mac)
                    macvendorlist.append(maclookup2(mac))
                    maclist.append(mac)
                    try:
                        maciplist.append(arpdict[mac])
                    except KeyError:
                        maciplist.append('na')
            #
            if vmac and vmac != 'na':
                try:
                    vmacip = arpdict[vmac]
                except KeyError:
                    vmacip = ''
                vmacvendor = maclookup2(vmac)
            else:
                vmac = ''
            #
            if vlan == 'trunk':
                vlanname = 'trunk'
            elif vlan[0].isdigit():
                try:
                    vlanname = vlandict[vlan]
                except KeyError:
                    vlanname = "not found"
            else:
                vlanname = ''
            #
            # debug
            if args.debug and iface == 'Gi1/0/3':
                # Using a # to join to make it consistent. # is not used in the
                # OUI datase.
                print('Combine debug:', ip, iface, vlan, ifstatus, lastchange,
                      '#'.join(maclist),
                      '#'.join(maciplist),
                      '#'.join(macvendorlist),
                      vmac, vmacip, vmacvendor)
            # creating a new list with all information.
            # Using a # to join to make it consistent. # is not used in the
            # OUI datase.
            macipvendor.append('{};{};{};{};{};{};{};{};{};{};{};{}'.format(
                iface, ifdesc, vlan, vlanname, ifstatus, lastchange,
                '#'.join(maclist),
                '#'.join(maciplist),
                '#'.join(macvendorlist),
                vmac, vmacip, vmacvendor))
        # IF, VLAN, VLANNAME, IFSTATE, MAC, MACIP, MACVENDOR, VMAC,
        # VMACIP, VMACVENDOR=
        #
        # Setting the new entry in the global dict.
        allswitchinfo[ip] = [hostname, macipvendor, snmplocation, uptime]


def createexcel(filename):
    headerwidth = [11, 25, 8, 24, 14, 16, 16, 16, 36, 16, 16, 36]
    headerlist = (
        'Interface;IF Description;VLAN;VLAN Name;IF status;Last change;' +
        'Data MAC;Data IP;Data vendor;Voice MAC;Voice IP;Voice vendor')
    headertotal = len(headerlist.split(';'))-1

    # create the workbook
    workbook = xlsxwriter.Workbook(filename)
    header = workbook.add_format()
    header.set_bold()
    header.set_align('vcenter')
    # Wrap text format
    wt = workbook.add_format()
    wt.set_text_wrap()
    wt.set_align('vcenter')
    # setting default format
    defformat = workbook.add_format()
    defformat.set_align('vcenter')
    red = workbook.add_format()
    red.set_align('vcenter')
    red.set_color("red")
    #
    worksheet = workbook.add_worksheet('info')
    worksheet.set_default_row(16)
    worksheet.set_column('{0}:{0}'.format('A'), 14)
    worksheet.set_column('{0}:{0}'.format('B'), 30)
    worksheet.set_column('{0}:{0}'.format('C'), 40)
    row = 0
    col = 0
    #
    worksheet.write(row, col, 'Info', header)
    row += 1
    worksheet.write(row, col, '''This excel provides information about the
status of interfaces,the MAC address of active endpoints, the related IP
address and the vendor information (if known).''', defformat)
    row += 2
    worksheet.write(row, col, '''Interface status information:''', header)
    row += 1
    intfstatus = '''connected: A device is connected
notconnect: No active device is connected
disabled: Interface is administratively disabled
trunk: Interface is not an access port. Ability to support multiple\
 vlans.
err-disabled: An error has occured on the interface. Depending on the\
 error this will automatically be restored.
routed: A layer 3 enabled interface. Not vlan related.'''
    for x in intfstatus.split('\n'):
        worksheet.write(row, col, x.split(':')[0], defformat)
        worksheet.write(row, col + 1, x.split(':')[1].lstrip(), defformat)
        row += 1
    row += 1
    worksheet.write(row, col, 'Last change port information:', header)
    row += 1
    worksheet.write(row, col, '''It shows the amount of days it has its current
 status. This can be useful for spotting long time unused ports.''')
    row += 1
    worksheet.write(row, col, '''If the "IF status" = notconnect and the last
 change date value is higher than the provided "days" (default 60) it is
 shown in red''')
    row += 2
    #
    worksheet.write(row, col, '''NOTE:''', header)
    row += 1
    noteinfo = ('It could be that not all connected interfaces have a MAC ' +
                'address shown.\nIt could happen that the device is not ' +
                'actively communicating on the network,\ntherefore the ' +
                'switch no longer is aware of the MAC address of the ' +
                'endpoint.')
    #
    for x in noteinfo.split('\n'):
        worksheet.write(row, col, x, defformat)
        row += 1
    #
    row += 1
    #
    worksheet.write(row, col, '''Devices:''', header)
    worksheet.write(row, col + 1, '''IP:''', header)
    worksheet.write(row, col + 2, '''SNMP location:''', header)
    row += 1
    for ip in sorted(allswitchinfo, key=lb.split_ip):
        col = 0
        worksheet.write(row, col, allswitchinfo[ip][0], defformat)
        worksheet.write(row, col + 1, ip, defformat)
        worksheet.write(row, col + 2, allswitchinfo[ip][2], defformat)
        row += 1
    #
    # row += 1
    #
    # Starting new tabs, for each IP address.
    for ip in sorted(allswitchinfo, key=lb.split_ip):
        row = 0
        col = 0
        hostname = allswitchinfo[ip][0]
        snmplocation = allswitchinfo[ip][2]
        uptime = allswitchinfo[ip][3]
        worksheet = workbook.add_worksheet('_'.join((hostname, ip)))
        # worksheet.set_default_row(16)
        # iface, vlan, ifstatus, vmac, ','.join(maclist)))
        for x in headerwidth:
            worksheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), x)
            col += 1
        col = 0
        #
        # placing some top info
        worksheet.write(row, col, 'Location: {}'.format(snmplocation))
        row += 1
        worksheet.write(row, col, 'Uptime: {}'.format(uptime))
        row += 1
        worksheet.write(row, col, 'Highlighted above: {} days'.format(
            str(reddays)))
        row += 2
        #
        beginrow = row
        tableheader = []
        for x in headerlist.split(';'):
            worksheet.write(row, col, x, header)
            tableheader.append({'header': x})
            col += 1
        #
        row += 1
        col = 0
        #
        for line in allswitchinfo[ip][1]:
            IF, DESC, VLAN, NAME, IFSTATE, LASTCHANGE, MAC, MACIP, MACVENDOR, \
                VMAC, VMACIP, VMACVENDOR = line.split(';')
            worksheet.write(row, col, IF, defformat)
            worksheet.write(row, col + 1, DESC, defformat)
            worksheet.write(row, col + 2, VLAN, defformat)
            worksheet.write(row, col + 3, NAME, defformat)
            worksheet.write(row, col + 4, IFSTATE, defformat)
            if (int(LASTCHANGE.split()[0]) > reddays and
                    IFSTATE == 'notconnect'):
                worksheet.write(row, col + 5, LASTCHANGE, red)
            else:
                worksheet.write(row, col + 5, LASTCHANGE, defformat)
            worksheet.write(row, col + 6, MAC.replace('#', '\n'), wt)
            worksheet.write(row, col + 7, MACIP.replace('#', '\n'), wt)
            worksheet.write(row, col + 8, MACVENDOR.replace('#', '\n'), wt)
            worksheet.write(row, col + 9, VMAC.replace('#', '\n'), wt)
            worksheet.write(row, col + 10, VMACIP.replace('#', '\n'), wt)
            worksheet.write(row, col + 11, VMACVENDOR.replace('#', '\n'), wt)
            row += 1
            #
        #
        # Creating nice table headers.
        worksheet.add_table(beginrow, 0, row-1, headertotal,
                            {'columns': tableheader})

    # Closing the workbook, all IP's done.
    workbook.close()


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
parser.add_argument('-vv', '--voicevlan', required=False,
                    default=None, action='append',
                    help='''Provide an alternative voicevlan than 200.
                    Multiple times allowed.''')
parser.add_argument('-l3', required=True,
                    help='''Provide the core switch IP address.''')
parser.add_argument('-sc', required=True,
                    help='''Provide the site code.''')
parser.add_argument('-r', '--red', type=int,
                    default=60, required=False,
                    help='''The provided number is used for marking the
                    amount of days higher than this number.
                    Default is %(default)s. If no marking is desired,
                    use 0''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
parser.add_argument('--telnet', default=None, required=False,
                    action='store_true', help='''Use telnet instead of SSH.''')
parser.add_argument('--time', required=False, default=None,
                    action='store_true',
                    help='Show time information per task.')
parser.add_argument('--ouidb', required=False,
                    default='/home/dorlab01/oui/oui_short.txt',
                    help='This allow you to provide a different OUI database.')
parser.add_argument('--debug', required=False, default=None,
                    action='store_true',
                    help='Show debug information.')
args = parser.parse_args()

# Doing some time calculation
start = time.time()
# use the environment variables
communitystring = lb.envvariable("CISCOCOMMUNITY")
# subdir = time.strftime("%Y%m%d_%H%M%S")+"_"+args.sc+"_portmacip"
# today = datetime.date.today().strftime("%Y%m%d")
outputdir = os.getenv("HOME")+"/working/Portmacip"
# filename = '{}/{}_{}.xlsx'.format(outputdir, args.sc, today)
filename = '{}/{}_{}_portmacip.xlsx'.format(
    outputdir, time.strftime("%Y%m%d_%H%M%S"), args.sc)
q = Queue()
reddays = args.red
threads = list()
lock = threading.Lock()
allswitchinfo = dict()
macdict = dict()
delay = args.delay
acsprefix = args.acsprefix
devicetype = 'cisco_ios'
reMAC = re.compile(r'([0-9a-zA-Z]{4}\.[0-9a-zA-Z]{4}\.[0-9a-zA-Z]{4})')
reINT = re.compile('^[FGT][aie]\d/.*?\d{1,2} ')
# reINT = re.compile(
#     '^Gi\d/\d/\d{1,2} '
#     '|^Gi\d/\d{1,2} '
#     '|^Fa\d/\d/\d{1,2} '
#     '|^Fa\d/\d{1,2} '
#     '|^Te\d/\d/\d{1,2} '
#     '|^Te\d/\d{1,2} ')
if not args.voicevlan:
    voicevlan = ['200']
else:
    voicevlan = args.voicevlan
ouidict = dict()

if args.telnet:
    devicetype = 'cisco_ios_telnet'
if args.red == 0:
    reddays = 100000000

# create a dict of the ouifile
with open(args.ouidb) as f:
    for line in f:
        ouimac = line.strip('\n').split()[0]
        company = line.strip('\n').split('(base 16)')[1].lstrip()
        ouidict[ouimac] = company
#
# Creating the sub-directory to save the files
if not os.path.isdir(outputdir):
    os.mkdir(outputdir)

# Staring an x amount of threads
for x in range(args.processes):
    # calling the function threader
    t = threading.Thread(target=threader)
    t.start()
    threads.append(t)

# receive a list from the library. input can be an ip, iplist or hpov csv
iplist, iperror = lb.readipfile(args.ip)
if args.time:
    print("Got the iplist in", time.time() - start, 'seconds')

print('starting with L2 access switches')
# Running through the IP addresses
for ip in iplist:
    # Putting the ip in the queue
    # print ("putting the", ip, "to the queue")
    q.put(ip)

# wait until the thread terminates
q.join()

if args.time:
    print("All L2 information received in", time.time() - start, 'seconds')

# stop workers
for i in range(args.processes):
    q.put(None)
for t in threads:
    t.join()

# connect to the L3 core switch to retrieve the arp list
print('getting the arp list')
arpdict, vlandict = l3info(args.l3)
# print('arpdict:\n', arpdict)
# print('vlandict:', vlandict)

if args.time:
    print("All L3 information received in", time.time() - start, 'seconds')

# Combine the information of L2 and L3 and do vendor lookups.
print('Combine the information: combinel2arpvendor')
combinel2arpvendor(arpdict)
# print('arplist:')
# for x in arplist:
#     print(x)

if args.time:
    print("L2, L3 and vendor information combined in",
          time.time() - start, 'seconds')


# print('allswitchinfo:')
# print(allswitchinfo)

# create the excel based on all information.

# for ip in allswitchinfo:
#     print('\n', '*'*10, ip, '*'*10, '\n')
#     for y in allswitchinfo[ip][1]:
#         if 'connected' in y:
#             print(y)

# All information gathered. Now creating the excel file.
print('Creating the excel sheet')
createexcel(filename)

if args.time:
    print("Excel file created in",
          time.time() - start, 'seconds')

print("\nTotal devices done: {}".format(len(iplist)))
print("The output file is located at:")
print("  ", filename)

# Print an error for IP's that couldn't be processed.
if iperror:
    print("\n\nThe following lines from the source were not used because of \
errors:\n")
    for x in iperror:
        print(x)
