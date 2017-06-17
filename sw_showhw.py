#!/usr/bin/env python3
'''
Bash environment variables used:
- CISCOCOMMUNITY
'''
import argparse
import os
import sys

from mylib import libbart as lb


# To do
# arg.parse output dir

# Provide switches to control this script
parser = argparse.ArgumentParser(
    description='''
    This program is used to provide a quickview on the existing hardware device
    types.
    ''',
    epilog="Bash environment variables used: CISCOCOMMUNITY")
parser.add_argument(
    '-i', '--ip', required=True, help="Input should \
    be an IP address, a file containing IP addresses or an HPov csv export \
    #file.")
parser.add_argument(
    '-fn', '--filename', required=False, default=None,
    help="Provide only the output filename. The directory is set to: \
    ~/ISE_SW/.If none is provided the output will be printed to the screen.")
parser.add_argument(
    '--dir', required=False, default=None,
    help="Provide the directory. The default directory is set to: %(default)s."
    )
parser.add_argument(
    '--ISE', required=False, default=None,
    action='store_const', const='yes',
    help='''If provided this will generate an overview of the compliant \
    hardware.''')
parser.add_argument('--acsprefix', required=False, default=None,
                    help='''Provide a prefix to read a different set of
                    environemnt variables than the default.''')
parser.add_argument('--telnet', default=None, required=False,
                    action='store_true', help='''Use telnet instead of SSH.''')
args = parser.parse_args()

acsprefix = args.acsprefix
devicetype = 'cisco_ios'
iplist, iperror = lb.readipfile(args.ip)
if not iplist:
    sys.exit("No IP('s) found/given. Exiting.")
# today = time.strftime("%Y%m%d")
timeout = 1
# q = Queue()
# lock = threading.Lock()
processes = 30
errorlist = []
swlist = []
iosdict = {}
totall1, totall2, totall3, totalios = 0, 0, 0, 0
nonise = ('2950', '2970', '2960S-24TS-S', '2960S-48TS-S', '3550',
          '2960G')
prefmigrate = ('3560-', '3750-')
goodios = ('c2960s-universalk9-mz.122-58.SE2.bin',
           'c2960x-universalk9-mz.152-2.E4.bin',
           'c3560-ipbasek9-mz.122-55.SE4.bin',
           'c3750-ipbasek9-mz.122-55.SE4.bin',
           'c3750-ipbasek9-mz.122-58.SE2.bin',
           'c3750e-universalk9-mz.122-58.SE2.bin',
           'c2960-lanbasek9-mz.122-58.SE2.bin')
if args.dir:
    outputdir = args.dir
else:
    outputdir = '{}/ISE_SW/'.format(os.getenv("HOME"))
outputfile = args.filename
outputfileloc = outputfile
if outputfile and not os.path.isdir(outputdir):
    os.mkdir(outputdir)

fileopened = None
if args.telnet:
    devicetype = 'cisco_ios_telnet'
if outputfile:
    outputfile = open('{}/{}'.format(outputdir, outputfile), 'a')
    fileopened = True
    print('Limited information is printed on the screen, \
because an output file is used.')
    print('The output is added if the file existed. \
Output dir: {}\nLocation of the outputfile: {}'.format(outputdir,
                                                       outputfileloc))
else:
    outputfile = sys.stdout
# import pdb; pdb.set_trace()

# Test ip
# ip='10.207.137.254'

for ip in iplist:
    # if ip.endswith('254'):
    #     continue
    print("IP:", ip)
    try:
        sw = lb.Switch(ip, timeout=6, acsprefix=acsprefix)
    except ConnectionError as err:
        print("Couldn't get data from this IP:", ip, "with error:", err,
              file=outputfile)
        continue
    except:
        print("There has been an issue with IP:", ip, "  - skipped",
              file=outputfile)
        print("Error received:", sys.exc_info()[0], file=outputfile)
        continue
    # print(sw.typeoid)
    print("Hostname: {}, IP: {}".format(sw.gethostname(), ip), file=outputfile)
    ios = sw.getioslocfile()
    print("IOS: {}".format(ios), file=outputfile)
    # print("sw.hardwaregroup", sw.hardwaregroup)
    if sw.hardwaregroup == 3:
        slots = sw.getdevicetype()
        for blade in slots:
            print("HW: {}:\t{}".format(blade, slots[blade]), file=outputfile)
    elif sw.hardwaregroup:
        iosdict[ip] = ios
        for stack in range(0, sw.getstackamount()):
            swtype = sw.getdevicetype()['sw{}'.format(str(stack+1))]
            swlist.append(swtype)
            print("HW: {}".format(swtype), file=outputfile)
    else:
        print('IP has no hardwaregroup, not added to iosdict')
        print("HW: {}".format(sw.getdevicetype()), file=outputfile)

if args.ISE:
    print(
        "\n***************************************\n\
Totals: (excluding modular devices)", file=outputfile)
    l1, l2, l3 = [], [], []
    for x in set(swlist):
        for y in nonise:
            if x.find(y) >= 0:
                l1.append(x)
        for y in prefmigrate:
            if x.find(y) >= 0:
                l2.append(x)
        if not (x in l1 or x in l2):
            l3.append(x)

    if set(l1):
        print('Switches that are not ISE supported and require an upgrade:',
              file=outputfile)

    for x in set(l1):
        print('Replace: HW: {:<18} Amount: {}'.format(
            x, swlist.count(x)), file=outputfile)
        totall1 += swlist.count(x)
    #
    if set(l2):
        print('\nSwitches that are preferred to be upgraded:', file=outputfile)

    for x in set(l2):
        print('PrefUpg: HW: {:<18} Amount: {}'.format(
            x, swlist.count(x)), file=outputfile)
        totall2 += swlist.count(x)
    #
    if set(l3):
        print('\nThe following switches are fine:', file=outputfile)

    for x in set(l3):
        print('Fine:    HW: {:<18} Amount: {}'.format(
            x, swlist.count(x)), file=outputfile)
        totall3 += swlist.count(x)
    #
    # if iosdict:
    #     print('\nIncorrect IOSes:', file=outputfile)

    faultyios = {}
    for x in iosdict:
        if not iosdict[x].split('/')[-1].split(':')[-1] in goodios:
            faultyios[x] = iosdict[x].split('/')[-1].split(':')[-1]
            # print('IP: {}, IOS: {}'.format(
            #     x,
            #     iosdict[x].split('/')[-1]),
            #     file=outputfile)

    if faultyios:
        print('\nIncorrect IOSes on access switches:', file=outputfile)
        for x in faultyios:
            print('IP: {:<15} IOS: {}'.format(
                x, faultyios[x]), file=outputfile)
        totalios += 1

    if totall1 or totall2 or totall3 or totalios:
        print('\nTotal SW information:', file=outputfile)
        print('Fine: {:>3} PrefUpgrade: {:>3} Replace: {:>3} \
IOS update: {:>3}'.format(
            totall3, totall2, totall1, totalios), file=outputfile)

if fileopened:
    outputfile.close()
