#!/usr/bin/env python3
import argparse
import os
import re
import sys
import time

import xlsxwriter

from mylib import libbart as lb


# Provide switches to control this script
parser = argparse.ArgumentParser(
    # Usage="%(prog)s [options] ; Use -h to show all options.",
    add_help=True,
    description='''
    This program is used to gather all the information needed
    to fill the cmdb.
    ''',
    epilog="Bash environment variables used: CISCOCOMMUNITY")
parser.add_argument('-i', '--ip', required=True, help="Input should be an \
                    IP address, a file containing IP addresses or an HPov \
                    csv export file.")
parser.add_argument('--blades', required=False, action='store_const',
                    const='yes', help="Set this if you to include blades of a 4 \
                    500/6500.")
args = parser.parse_args()
arg1 = args.ip
argblades = None
if args.blades:
    argblades = args.blades
iplist, iperror = lb.readipfile(arg1)

# Provide communitystring for SNMP
communitystring = lb.envvariable("CISCOCOMMUNITY")

# Sets the user that will be filled into the Excel "UserID" column
user = 'KuperP01'

# If any errors are found in reading the ip file print them
for x in iperror:
    print(x)

# Set outputdir if iplist exists, count total IPs
if iplist:
    totalip = len(iplist)
    workdir = os.path.expanduser('~') + '/working'
    currenttime = time.strftime("%Y%m%d_%H%M%S")
    outputdir = workdir + "/" + currenttime + "_cmdb" + "/"
else:
    sys.exit("No valid IPs.")

# Variables that will be used later in this file
count = 0
xlsxrows = []
sites = []

# Start the clock
start = time.time()

# For each ip do the following:
for ip in iplist:
    count += 1

    # Print the status
    print('{}/{} - Starting with IP: {}'.format(count, totalip, ip))

    # Use the class Switch in libbart to use it's functions
    try:
        sw = lb.Switch(ip)
    except:
        print('{} - Error: no response received before timeout'.format(ip))
        continue
    hostname = sw.gethostname()
    l1 = []
    output = []
    loc = ''
    tagdict, tagerror = sw.gettag(argblades)
    if tagerror:
        for x in tagerror:
            print(x)

    # Check if the amount of returned serials is equal to
    # the amount of switches
    stackamount = sw.getstackamount()
    serialamount = len(sw.getserial())
    if serialamount is not stackamount and sw.hardwaregroup is not 3:
        print('{} - Found {} serial(s) and {} switch(es) \
please check'.format(ip, serialamount, stackamount))
        continue

    # Get siteID and room location of switch via SNMP.
    loc = sw.getlocation()
    reg = re.compile('[A-Za-z]{5}[0-9]{2}')
    if re.search(reg, loc):
        site = re.search(reg, loc).group()
        if site and site not in sites:
            sites.append(site)
        room = loc.replace(site, '').strip(', ')
    else:
        site = 'SiteID not found please check manually. \
                Output SNMP: {}'.format(loc)
        room = loc

    # if hardware is 4500 or 6500
    if sw.hardwaregroup == 3:
        output = lb.getcmdoutput(
            ip, 'show run | b banner exec').split('\n')
        reg = re.compile('\*.*?(?i)tag:.*?([0-9]{4,8})')
        slot = sw.snmp.get('1.3.6.1.2.1.47.1.1.1.1.7.1')

        # if VSS: get serial, tag, type, switch1 or 2 in VSS per switch
        if sw.snmp.get('1.3.6.1.2.1.47.1.1.1.1.7.1') == 'Virtual Stack':
            # slot = sw.snmp.get('1.3.6.1.2.1.47.1.1.1.1.7.2')
            devtype = sw.snmp.get('iso.3.6.1.2.1.47.1.1.1.1.13.2')
            serial = sw.snmp.get('1.3.6.1.2.1.47.1.1.1.1.11.2')
            # slot2 = sw.snmp.get('1.3.6.1.2.1.47.1.1.1.1.7.500')
            devtype2 = sw.snmp.get('iso.3.6.1.2.1.47.1.1.1.1.13.500')
            serial2 = sw.snmp.get('1.3.6.1.2.1.47.1.1.1.1.11.500')
            tag1 = tagdict[serial]
            tag2 = tagdict[serial2]
            xlsxrows.append([tag1, hostname, devtype, 'Cisco', site, room,
                             'Corporate ICT', user, 'production', serial])
            xlsxrows.append([tag2, hostname, devtype2, 'Cisco', site, room,
                             'Corporate ICT', user, 'production', serial2])

        # If single 4500/6500 get serial, tag, type
        else:
            # slot = sw.snmp.get('1.3.6.1.2.1.47.1.1.1.1.7.1')
            serial = sw.snmp.get('1.3.6.1.2.1.47.1.1.1.1.11.1')
            tag = tagdict[serial]
            devtype = sw.snmp.get('iso.3.6.1.2.1.47.1.1.1.1.13.1')
            xlsxrows.append([tag, hostname, devtype, 'Cisco', site, room,
                             'Corporate ICT', user, 'production', serial])

        # Retrieve information from blades in 4500/6500 if argument --blades
        # is set.
        if argblades:
            bladeserial = sw.getbladeserial()
            for x in bladeserial:
                serial = bladeserial[x][1]
                devtype = bladeserial[x][0]
                tag = tagdict[serial]
                # slot = x
                xlsxrows.append([tag, hostname, devtype, 'Cisco', site, room,
                                 'Corporate ICT', user, 'production', serial])
    # If not a 4500 or 6500
    else:
        if not sw.getserial():
            print('{} - no serial found please add type {} to libbart'.format(
                ip, sw.typeoid[-1]))
            continue

        for y, x in enumerate(sw.getserial()):
            serial = sw.getserial()['sw{}'.format(y + 1)]
            devtype = sw.getdevicetype()['sw{}'.format(y + 1)]
            reg = re.compile('SW\d{4,6}')
            tag = tagdict[serial]
            xlsxrows.append([tag, hostname, devtype, 'Cisco', site, room,
                             'Corporate ICT', user, 'production', serial])

# Create output dir to save Excel file in
if not os.path.isdir(outputdir):
    os.mkdir(outputdir)
totalrows = len(xlsxrows)

# Create Excel file with data
if len(iplist) == 1:
    filename = '{}{}_cmdb.xlsx'.format(outputdir, iplist[0])
elif len(sites) == 1:
    filename = '{}{}_cmdb.xlsx'.format(outputdir, site)
else:
    filename = '{}multiple_sites_cmdb.xlsx'.format(outputdir)
workbook = xlsxwriter.Workbook(filename)

for site in sites:
    siterows = []
    for row in xlsxrows:
        if site == row[4]:
            siterows.append(row)
    worksheet = workbook.add_worksheet(site)
    column_width = {'A:A': 20, 'B:B': 10, 'C:C': 25, 'D:D': 8, 'E:E': 10,
                    'F:F': 20, 'G:G': 15, 'H:H': 6, 'I:I': 15, 'J:J': 15}
    for x in column_width:
        worksheet.set_column(x, column_width[x])

    worksheet.add_table('A3:J{}'.format(3 + len(siterows)),
                        {'data': siterows,
                         'columns': [{'header': 'Tagnumber'},
                                     {'header': 'DNS Name'},
                                     {'header': 'Product'},
                                     {'header': 'Product supplier'},
                                     {'header': 'Building'},
                                     {'header': 'Building-room'},
                                     {'header': 'Opco'},
                                     {'header': 'UserID'},
                                     {'header': 'Status'},
                                     {'header': 'Serial number'},
                                     ]})
workbook.close()

# end time - start time
print("\n\nTotal time:", time.time() - start)
if os.path.isdir(outputdir):
    print("The output is saved in:\n", outputdir)
else:
    print("Nothing is written.")
