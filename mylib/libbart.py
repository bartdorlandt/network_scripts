'''
This library is used for all network scripts.
It lists different functions that are used by several scripts.


'''
import re
import os
import sys
import hnmp
from netmiko import ConnectHandler
from netmiko.ssh_exception import (NetMikoTimeoutException,
                                   NetMikoAuthenticationException)
from collections import OrderedDict
from getpass import getpass
# from IPy import IP


def checkip(ip):
    ipre = re.compile('^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                      '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    if ipre.match(ip):
        return ip
    else:
        return None


def readipfile(iparg):
    '''This module will return a list with the ip addresses and a list with
    errors. It can handle a single ip address, a file containing ip addresses
    or an HPov csv file.'''
    iplist = []
    iperror = []
    ipre = re.compile('((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                      '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')
    # subnet mask option /8 - /32 possibilities.
    # ipresubnet = re.compile('((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    #                   '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/'
    #                   '([1-2][0-9]|3[0-2]|[8-9])')
    # First check if it is an ip address. If so, add it to the list
    # if ipresubnet.match(iparg):
    #     iplist = [x for x in IP(iparg)]
    if ipre.match(iparg):
        iplist.append(iparg)
    elif os.path.isfile(iparg):
        # open the file and see if it is a HPOV csv or just IPs.
        # Add them to the list
        with open(iparg, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or line.startswith("!") or not line:
                    continue
                elif line.startswith("Status"):
                    # print("line starts with a #")
                    continue
                elif ipre.search(line):
                    ip = ipre.search(line).group(0)
                    iplist.append(ip)
                else:
                    iperror.append("This line is not used: {}".format(line))
    else:
        iperror.append("Not an IP or an existing file: {}".format(iparg))

    return iplist, iperror


def readipfile_OLD(iparg):
    '''This module will return a list with the ip addresses and a list with
    errors. It can handle a single ip address, a file containing ip addresses
    or an HPov csv file.'''
    iplist = []
    iperror = []
    ipre = re.compile('^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                      '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    # First check if it is an ip address. If so, add it to the list
    if ipre.match(iparg):
        iplist.append(iparg)
    elif os.path.isfile(iparg):
        # open the file and see if it is a HPOV csv or just IPs.
        # Add them to the list
        with open(iparg, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("Normal") or line.startswith("Minor"):
                    ip = line.split(',')[3]
                    if ipre.match(ip):
                        iplist.append(ip)
                    else:
                        iperror.append("This line is not used: {}".format(
                            line))
                elif ipre.match(line):
                    iplist.append(line)
                elif line.startswith("Status"):
                    # print("line starts with a #")
                    continue
                elif line.startswith("#"):
                    # print("line starts with a #")
                    continue
                elif not line:
                    # print("line is empty")
                    continue
                else:
                    iperror.append("This line is not used: {}".format(line))
    else:
        iperror.append("Not an IP or an existing file: {}".format(iparg))

    return iplist, iperror


def envvariable(variable, prefix=None):
    '''Read the information either from the bash environment variables or use
    the input() function to retrieve it from the user.
    It returns a string with the variable information.'''
    if prefix:
        variable = prefix+variable
    try:
        envvar = os.environ[variable]
    except KeyError:
        # envvar = input(
        print(
            '[-] No environment variable was found for the ' +
            'environment variable: {}.\n'.format(variable) +
            '[-] Add it to your environment variables and restart the ' +
            'session or provide it manually.\n')
        envvar = getpass(prompt='variable {}: '.format(variable))
        os.environ[variable] = envvar
    return envvar


class Switch(object):

    '''The IP address should be provided. With this it can deliver information
    from the switch, like the hostname'''

    def __init__(self, ip, timeout=4, acsprefix=None, delay_factor=1.0):
        self.ip = ip
        self.acsprefix = acsprefix
        self.delay_factor = delay_factor
        # Getting the community from the other functions
        self.snmp = hnmp.SNMP(ip,
                              community=envvariable("CISCOCOMMUNITY",
                                                    self.acsprefix),
                              timeout=timeout)
        self.mibserial = '1.3.6.1.2.1.47.1.1.1.1.11'
        try:
            type = self.snmp.get('1.3.6.1.2.1.1.2.0').getOid()._value[-1]
        except hnmp.SNMPError:
            raise ConnectionError('SNMP')
        self.typeoid = self.snmp.get('1.3.6.1.2.1.1.2.0').getOid()
        # import pdb; pdb.set_trace()
        if type in (1208,):
            self.i = 1001
            self.hardware = '2960(SX,)'
            self.hardwaregroup = 1
            self.stack = 1
            self.managedswitch = 1
        elif type in (694, 695, 716, 1016, 950, 1257, 696, 951, 799, 927, 928,
                      1146, 717, 1752):
            self.i = 1001
            self.hardware = '2960'
            self.hardwaregroup = 1
            self.stack = 0
            self.managedswitch = 0
        elif type in (798, 1365):
            self.i = 1001
            self.hardware = '2960-8'
            self.hardwaregroup = 1
            self.stack = 0
            self.managedswitch = 0
        elif type in (1367,):
            self.i = 1001
            self.hardware = '2960-12'
            self.hardwaregroup = 1
            self.stack = 0
            self.managedswitch = 0
        elif type in (2066, ):
            self.i = 1000
            self.hardware = '3650'
            self.hardwaregroup = 1
            self.stack = 1
            self.managedswitch = 1
        elif type in (516,):
            self.i = 1001
            self.hardware = '3750'
            self.hardwaregroup = 1
            self.stack = 1
            self.managedswitch = 1
        elif type in (959,):
            self.i = 1001
            self.hardware = 'IE-3000-8TC'
            self.hardwaregroup = 1
            self.stack = 0
            self.managedswitch = 1
        elif type in (563, 564, 633, 615, 617, 1021, 614, 1025, 634, 795, 796,
                      616, 1228, 1024, 797, 1229):
            self.i = 1001
            self.hardware = '3560'
            self.hardwaregroup = 1
            self.stack = 0
            self.managedswitch = 1
        elif type in (1732, 1287, 875, 503, 502, 501, 659):
            self.i = 1000
            self.hardware = '4500'
            self.mibslot = '1.3.6.1.2.1.47.1.1.1.1.7'
            self.stack = 0
            self.managedswitch = 1
            self.hardwaregroup = 3
        elif type in (896, 283):
            self.i = 1000
            self.hardware = '6500'
            self.mibslot = '1.3.6.1.2.1.47.1.1.1.1.7'
            self.stack = 0
            self.managedswitch = 1
            self.hardwaregroup = 3
        elif type in (323, 429, 480, 325, 428, 324, 560, 359):
            self.i = 1
            self.hardware = '2950'
            self.hardwaregroup = 4
            self.stack = 0
            self.managedswitch = 0
        elif type in (561,):
            self.i = 1001
            self.hardware = '2970'
            self.hardwaregroup = 4
            self.stack = 0
            self.managedswitch = 0
        elif type in (278,):
            self.i = 1
            self.hardware = '3548'
            self.hardwaregroup = 4
            self.stack = 0
            self.managedswitch = 1
        elif type in (431, 366):
            self.i = 1
            self.hardware = '3550'
            self.hardwaregroup = 4
            self.stack = 0
            self.managedswitch = 0
        elif type in (748,):
            self.i = 1001
            self.hardware = 'CBS3020'
            self.hardwaregroup = 4
            self.stack = 0
            self.managedswitch = 1
        else:
            self.i = 1000
            self.hardware = 'unknown'
            self.stack = 0
            self.managedswitch = 0
            self.hardwaregroup = 0

    def __getrange(self):
        if self.hardwaregroup == 1:
            amount = self.getstackamount()
        elif self.hardwaregroup == 3:
            # 1000-10000 - linecard 1 - 10 Switch1
            # 11000-20000 - linecard 1 - 10 Switch2
            amount = 20
        else:
            amount = 1
        return amount

    def __getmibhardware(self):
        if self.hardwaregroup == 1:
            mib = '1.3.6.1.2.1.47.1.1.1.1.2'
        elif self.hardwaregroup == 3:
            mib = '1.3.6.1.2.1.47.1.1.1.1.13'
        elif self.hardwaregroup == 4:
            mib = '1.3.6.1.2.1.47.1.1.1.1.13'
        else:
            print('{}. default mib chosen'.format(self.ip))
            mib = '1.3.6.1.2.1.47.1.1.1.1.2'
        return mib

    def __get(self, mib):
        l1 = []
        y = self.__getrange()
        count = self.i
        for dev in range(0, y):
            output = self.snmp.get('{}.{}'.format(mib, count))
            if output:
                l1.append(output)
            count += 1000
        return l1

    def getstackamount(self):
        # info:
        # http://www.nycnetworkers.com/management/monitor-cisco-switch-stack-using-snmp/
        if self.stack:
            mib = '1.3.6.1.4.1.9.9.500.1.2.1.1'
            stackactive = self.snmp.table(
                mib,
                columns={6: "Operational"},
                fetch_all_columns=False)
            amount = len(stackactive.columns['Operational'])
        else:
            amount = 1
        return amount

    def gethostname(self):
        return self.snmp.get('1.3.6.1.4.1.9.2.1.3.0')

    def getlocation(self):
        return self.snmp.get('1.3.6.1.2.1.1.6.0')

    def getfqdn(self):
        return self.snmp.get('1.3.6.1.2.1.1.5.0')

    def getioslocfile(self):
        # works for 2960, 4500
        return self.snmp.get('1.3.6.1.2.1.16.19.6.0')

    def getdevicetype(self):
        mib = self.__getmibhardware()
        swdict = OrderedDict([])
        #
        if self.hardwaregroup == 3:
            l1 = self.__get(mib)
            l2 = self.__get(self.mibslot)
            for x, y in enumerate(l1):
                swdict[l2[x]] = l1[x]
        else:
            l1 = self.__get(mib)
            for x, y in enumerate(l1):
                swdict['sw{}'.format(x + 1)] = l1[x]
        return swdict

    def getserial(self):
        mib = self.mibserial
        swdict = OrderedDict([])
        if self.hardware == 4500:
            l1 = self.__get(mib)
            l2 = self.__get(self.mibslot)
            for x, y in enumerate(l1):
                swdict[l2[x]] = l1[x]
        else:
            l1 = self.__get(mib)
            for x, y in enumerate(l1):
                swdict['sw{}'.format(x + 1)] = l1[x]
        return swdict

    def getbladeserial(self):
        mib = self.__getmibhardware()
        mib2 = self.mibserial
        swdict = OrderedDict([])

        if self.hardwaregroup == 3:
            l1 = self.__get(mib)
            l2 = self.__get(self.mibslot)
            l3 = self.__get(mib2)
            for x, y in enumerate(l1):
                swdict[l2[x]] = [l1[x], l3[x]]
        else:
            l1 = self.__get(mib)
            l3 = self.__get(mib2)
            for x, y in enumerate(l1):
                swdict['sw{}'.format(x + 1)] = [l1[x], l3[x]]

        return swdict

    def gettag(self, argblades=None):
        '''This function returns an ordered dict which matches
        serial numbers to tags.'''
        tagdict = OrderedDict([])
        output = []
        tagerror = []
        seriallist = self.getserial()
        hostname = self.gethostname()

        if self.hardwaregroup == 3:
            output = getcmdoutput(
                self.ip, 'show run | b banner exec').split('\n')
            reg = re.compile('\*.*?(?i)tag:.*?([0-9]{4,8})')
            reg2 = re.compile('SW(\d{4,6})')
            reg3 = re.compile('SW(\d{4,6}).*?SW(\d{4,6})')
            tag = []
            for x in output:
                match = re.search(reg, x)
                if match and 'SN:' not in x:
                    tag.append(match.group(1))

            if not tag:
                for x in output:
                    match2 = re.search(reg3, x)
                    if match2 and 'SN:' not in x:
                        tag.append(match2.group(1))
                        tag.append(match2.group(2))
                if not tag:
                    match1 = re.search(reg2, hostname)
                    if match1:
                        tag.append(match1.group(1))

            if self.snmp.get('1.3.6.1.2.1.47.1.1.1.1.7.1') == 'Virtual Stack':
                serial = self.snmp.get('1.3.6.1.2.1.47.1.1.1.1.11.2')
                serial2 = self.snmp.get('1.3.6.1.2.1.47.1.1.1.1.11.500')
                if len(tag) is not 2:
                    tagerror.append('{} : not all tags found'
                                    .format(self.ip))
                    if not tag:
                        tag.append('no tag found')
                    tag.append('no tag found')
                if serial:
                    tagdict[serial] = tag[0]
                else:
                    tagerror.append('{} : no serial found for switch1'
                                    .format(self.ip))
                if serial2:
                    tagdict[serial2] = tag[1]
                else:
                    tagerror.append('{} : no serial found for switch2'
                                    .format(self.ip))

            else:
                serial = self.snmp.get('1.3.6.1.2.1.47.1.1.1.1.11.1')
                tagdict[serial] = tag[0]
            if argblades:
                bladeserial = self.getserial()
                for x in bladeserial:
                    serial = bladeserial[x]
                    reg1 = re.compile('\*.*?\[[0-9]{1,2}].*?' + serial)
                    reg2 = re.compile('\*.*?\[[0-9]{1,2}].*?' + serial +
                                      '.*?(?i)tag:.*?([0-9]{4,8})')

                    for x in output:
                        match1 = re.search(reg1, x)
                        if match1:
                            match2 = re.search(reg2, x)
                            if match2:
                                tagdict[serial] = match2.group(1)
                    if serial not in tagdict:
                        tagdict[serial] = 'no tag found'
                        tagerror.append(
                            '{} : no tag found for serial {}'.format(
                                self.ip, serial))
        else:
            reg = re.compile('SW\d{4,6}')
            for y, x in enumerate(seriallist):
                serial = seriallist['sw{}'.format(y + 1)]
                if re.search(reg, hostname) and self.getstackamount() == 1:
                    tagdict[serial] = hostname.split("SW")[1]
                else:
                    reg2 = re.compile('\*.*?\[[0-9]{1,2}].*?(?i)tag:.*?' +
                                      '([0-9]{4,8}).*' + serial)
                    if not output:
                        output = getcmdoutput(
                            self.ip, 'show run | b banner exec').split('\n')
                    for x in output:
                        match = re.search(reg2, x)
                        if match:
                            tagdict[serial] = match.group(1)

                if serial not in tagdict:
                    tagdict[serial] = 'no tag found'
                    tagerror.append(
                        '{} : no tag found in banner for serial {}'.format(
                            self.ip, serial))
        return tagdict, tagerror
        # def get4500slot(self):
        #     if self.hardware == 4500:
        #         l2 = self.__get(self.mibslot)
        #         l3 = []
        #         for x in l2:
        #             switch = x.split()[0]
        #             slotnum = x.split()[2]
        #             l3.append('{} slot {}'.format(switch, slotnum))
        #             return l3


def l2_only_vlans(ip, delay_factor=1.0, acsprefix=None,
                  device='cisco_ios'):
    l2vlanlist = []
    l3vlanlist = []
    cmd = ['sh ip int brie | i ^Vlan', 'sh vlan br']
    cmdoutput = getcmdoutput(
        ip, cmd,
        delay_factor=delay_factor,
        acsprefix=acsprefix,
        device=device)

    if not cmdoutput:
        sys.exit('no output received from the switch. Exiting')

    for x in cmdoutput.split('\n'):
        if x.startswith('Vlan'):
            l3vlanlist.append(int(x.split()[0][4:]))
        elif x[0].isdigit():
            if int(x.split()[0]) not in [1, 1002, 1003, 1004, 1005]:
                l2vlanlist.append(int(x.split()[0]))

    l2only = [item for item in l2vlanlist if item not in l3vlanlist]
    return l2only


def getcmdoutput(ip, cmd, device='cisco_ios',
                 strip_prompt=True, strip_command=True,
                 delay_factor=1.0, acsprefix=None):
    '''Get a string output for a list of commands send to an IP address. Device
    type cisco_ios is used by default.
    Other options are cisco_wlc or cisco_asa.'''
    output = ''
    if type(cmd) == str:
        cmd = cmd.split('\n')
    device = {
        'device_type': device,
        'ip': ip,
        'username': envvariable("ACSUSER", acsprefix),
        'password': envvariable("ACSPASS", acsprefix),
        'secret': envvariable("ACSENABLE", acsprefix),
        'verbose': False,
        'global_delay_factor': delay_factor,
    }
    try:
        net_connect = ConnectHandler(**device)
        output += net_connect.enable()
        for x in cmd:
            output += net_connect.send_command(
                '{}'.format(x),
                strip_prompt=strip_prompt,
                strip_command=strip_command)
        net_connect.disconnect()
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        print('Failed IP: {}, error: {}.'.format(ip, str(e)))
    return output


def uptime(ip, device='cisco_ios', acsprefix=None, delay_factor=1.0):
    '''This function retrieves a part of the 'show version' output including
    the uptime and minutes part. Therefore showing the complete period the
    device has been running.

    From this output it extracts the days and seconds, which it puts in the
    timedelta program. This way it can be used to do some calculations by
    other programs.

    The input is an IP address and the output is a timedelta time.

    It has a dependency on the function 'getcmdoutput', which is used to get
    the show version output.

    Example input:
        SW268000 uptime is 1 year, 14 weeks, 3 days, 21 hours, 37 minutes
    '''
    import datetime

    days = seconds = 0
    shver = getcmdoutput(ip, 'sh ver | i uptime',
                         delay_factor=delay_factor,
                         acsprefix=acsprefix,
                         device=device)
    uptimesplit = shver.replace(',', '').split()
    if uptimesplit[-1] in ('minute', 'minutes'):
        uptimesplit.pop()
        seconds = int(uptimesplit.pop()) * 60
    if uptimesplit[-1] in ('hour', 'hours'):
        uptimesplit.pop()
        seconds = seconds + (int(uptimesplit.pop()) * 3600)
    if uptimesplit[-1] in ('day', 'days'):
        uptimesplit.pop()
        days = days + int(uptimesplit.pop())
    if uptimesplit[-1] in ('week', 'weeks'):
        uptimesplit.pop()
        days = days + (int(uptimesplit.pop()) * 7)
    if uptimesplit[-1] in ('year', 'years'):
        uptimesplit.pop()
        days = days + (int(uptimesplit.pop()) * 365)
    return datetime.timedelta(days=days, seconds=seconds)


def getvlanports(shrun, vlan):
    '''Get all ports related to a certain vlan.'''
    from ciscoconfparse import CiscoConfParse
    if type(shrun) == list:
        parse = CiscoConfParse(shrun)
    elif type(shrun) == str:
        parse = CiscoConfParse(shrun.split('\n'))
    else:
        return None

    accessvlan = [
        x for x in parse.find_objects('^interface.+?thernet') if
        x.re_search_children('^ switchport access vlan {}$'.format(vlan))]
    l3vlan = [
        x for x in parse.find_objects('^interface.+?lan{}$'.format(vlan))
        if x.re_search_children('^ ip address ')]

    l2 = [x.text for x in accessvlan]
    l3 = [x.text for x in l3vlan]

    return l2, l3


def atoptr(iplist):
    from dns import reversename
    ptrlist = []
    for ip in iplist:
        ptrlist.append(reversename.from_address(ip).to_text())
    return ptrlist


def maxlength(l1):
    '''Getting the max length value of an iterable'''
    i = 0
    for x in l1:
        if len(x) > i:
            i = len(x)
    return i


def conf_range_gen(lines, step, debug=False):
    '''Generator to split the code while making sure it doesn't
    interrupt code blocks. 'lines' should be a long piece of text.
    Retrieved with f.readlines() for example.'''
    startincrease = 0
    totallines = len(lines)
    for x in range(0, totallines, step):
        start = x + startincrease
        configlines = lines[start:x + step]
        if debug:
            print('x, start, startincrease:', x, start, startincrease)
        if start + step >= totallines:
            # this is to catch the last part, to not be stuck in the while loop
            yield configlines
        else:
            i = 0
            while (configlines[-1] != '!\n' and
                   configlines[-1] != '!\r' and
                   configlines[-1] != '!' and
                   configlines[-1] != '\n' and
                   configlines[-1] != '\r' and
                   configlines[-1] != '\n\r'):
                # If the code doesn't end on a line that starts and ends with !
                # We will increase the length until we find one.
                # The next run of the for loop will have to increase with that
                # number to avoid errors of duplicate code.
                if debug:
                    print(configlines[-1])
                i += 1
                configlines = lines[start: x + step + i]
                if debug:
                    print('while configlines: %r' % configlines[-1])
                    print(len(configlines))
            startincrease = i
            yield configlines


def split_ip(ip):
    return tuple(int(part) for part in ip.split('.'))
