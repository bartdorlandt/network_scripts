'''This file should be called from another script.
It should provide provide at least 1 argument containing the parse of the
CiscoConfParse, the other can set the intrusive mode.
It will return a the CiscoConfParse list with configuration updates and an
error list.'''

# import sys
import re
from ciscoconfparse import CiscoConfParse


# General functions ####
# This module is used multiple times to verify the parent/child relation.
def parent_child_check(d1, d1sub, cfgdiffs):
    """
    d1 dictionary is used to verify and add certain commands to a interface
    d3 dictionary is used to remove certain commands from an interface
    d5 dictionary is used to default certain commands inside an interface
    The order should be starting with d5, then d3, then d1;
    therefore default, remove add information
    """

    fixit = None
    hasparent = None
    #
    if parse.find_children(d1):
        hasparent = 'yes'
        for sub in parse.find_children(d1):
            if sub == d1.strip('^$'):
                # print ('sub equals check')
                continue
    #        elif fixit == 'yes':
    #            break
    #            print ('fixit equals yes')
            if sub.strip() in d1sub.values():
                # print ('sub = ', sub)
                # print ('d1sub[x] = ', d1sub[x])
                continue
            else:
                fixit = 'yes'
                # print ('fixit is yes, break')
                break
        # print ('fixit == ', fixit)
    else:
        # print('fixit is set to yes')
        fixit = 'yes'
    if fixit == 'yes':
        # print ('fixit == yes , inside if')
        cfgdiffs.append_line('!')
        if hasparent == 'yes':
            cfgdiffs.append_line('no ' + d1.strip('^$'))
        cfgdiffs.append_line(d1.strip('^$'))
        for x in d1sub:
            cfgdiffs.append_line(' ' + d1sub[x])
    # end of repetetive code
    cfgdiffs.commit()
    return cfgdiffs


# Return correct stormcontrol value
def stormcontrol(intf):
    if intf.text.split(' ')[1].startswith('Fa'):
        stormlevel = '5.00'
    else:
        stormlevel = '2.00'
    return stormlevel


def addremoveintf(cfgdiffs, intf, d1=None, d3=None, d5=None, iprc=None):
    d2, d4, d6 = {}, {}, {}
    # d1 dictionary is used to verify and add certain commands to a interface
    # d3 dictionary is used to remove certain commands from an interface
    # d5 dictionary is used to default certain commands inside an interface
    # The order should be starting with d5, then d3, then d1;
    # therefore default, remove add information
    if d1:
        for x in d1.keys():
            d2[x] = intf.re_search_children(d1[x])
            if not d2[x]:
                d2[x] = 'docfg'
            else:
                del d2[x]
    #
    if d3:
        for x in d3:
            d4[x] = intf.re_search_children(d3[x])
            if not d4[x]:
                del d4[x]
    #
    if d5:
        for x in d5:
            d6[x] = intf.re_search_children(d5[x])
            if not d6[x]:
                del d6[x]
    #
    # If one of these exists, the interface is added along with any of
    # the values of these dictionaries.
    if d2 or d4 or d6 or iprc:
        cfgdiffs.append_line('!')
        cfgdiffs.append_line(intf.text)
        for x in d6:
            if d5[x].strip('^$').startswith(' no '):
                cfgdiffs.append_line(d5[x].strip('^$').replace(
                    ' no', ' default'))
            else:
                cfgdiffs.append_line(' default' + d5[x].strip('^$'))
        for x in d4:
            if d3[x].strip('^$').startswith(' no '):
                cfgdiffs.append_line(d3[x].strip('^$').replace(' no', ''))
            else:
                cfgdiffs.append_line(' no' + d3[x].strip('^$'))
            # print ('no ' + d3[x].strip('^$'))
        for x in d2:
            cfgdiffs.append_line(d1[x].strip('^$'))
        if iprc:
            cfgdiffs.append_line(' ip route-cache')
            cfgdiffs.append_line(' ip route-cache cef')
    #
    cfgdiffs.commit()
    return cfgdiffs


# All functions to check compliancy #####
def all(result, sw1=None, ip=None, hostname=None, intrusive=None):
    '''his modules is called from another script.
    It will call all other modules within this library and will return the
    config diff and an error list.'''
    #
    global parse, all_intfs, phys_intfs, unused_intfs, po_phys_intfs, error
    global l3vlan_intfs, swhostname
    parse = CiscoConfParse(result)
    cfgdiffs = CiscoConfParse([])
    all_intfs = []
    phys_intfs = []
    error = []
    swhostname = hostname
    #
    # Different methods are used to create these lists. Part of getting to know
    # the Ciscoconfparse code.
    #
    # creating a list for all shut/unused physical ports.
    # for obj in parse.find_objects('^interface.+?thernet'):
    #    if obj.re_search_children('shutdown'):
    #        unused_intfs.append(obj)
    #
    # Create an unused interfaces list
    unused_intfs = [x for x in parse.find_objects('^interface.+?thernet') if
                    x.re_search_children('shutdown')]
    #
    # creating a list po_phys_intfs
    po_phys_intfs = (
        parse.find_objects_w_child(
            parentspec=r"^interface.+?thernet",
            childspec=r"channel-group [0-9]"))
    #
    # creating a list for all other interfaces and physical interfaces.
    for x in parse.find_objects('^interface'):
        if x not in unused_intfs and x not in po_phys_intfs:
            all_intfs.append(x)
            if x.is_ethernet_intf:
                phys_intfs.append(x)

    # creating a list of l3vlan interfaces
    l3vlan_intfs = [x for x in parse.find_objects('^interface.+?lan[1-9]')]
    #
    # Calling all other modules
    main(sw1, ip)
    # cfgdiffs.append_line('! Starting global configuration')
    # cfgdiffs.commit()
    cfgdiffs = glconf(cfgdiffs, intrusive=intrusive)
    cfgdiffs = unusedint(cfgdiffs, intrusive=intrusive)
    cfgdiffs = glint(cfgdiffs, intrusive=intrusive)
    cfgdiffs = office(cfgdiffs, intrusive=intrusive)
    cfgdiffs = swtrunkpo(cfgdiffs, intrusive=intrusive)
    cfgdiffs = swtrunk(cfgdiffs, intrusive=intrusive)
    cfgdiffs = wlctrunk(cfgdiffs, intrusive=intrusive)
    cfgdiffs = dedvoice(cfgdiffs, intrusive=intrusive)
    cfgdiffs = dedvideo(cfgdiffs, intrusive=intrusive)
    cfgdiffs = l3vlan(cfgdiffs, intrusive=intrusive)
    cfgdiffs = waas(cfgdiffs, intrusive=intrusive)
    cfgdiffs = wan(cfgdiffs, intrusive=intrusive)
    cfgdiffs = wantrunk(cfgdiffs, intrusive=intrusive)
    cfgdiffs = fwfailover(cfgdiffs, intrusive=intrusive)
    cfgdiffs = fwpc(cfgdiffs, intrusive=intrusive)
    return cfgdiffs, error


def main(sw1, ip):
    global devicetype
    retype3 = re.compile('45[01][07]')
    retype2 = re.compile('3650')
    retype1 = re.compile('2960|3[57][56]0|65[0-9][0-9]|30[01][0-9]')
    if re.search(retype3, sw1):
        devicetype = 'type3'
    elif re.search(retype2, sw1):
        devicetype = 'type2'
    elif re.search(retype1, sw1):
        devicetype = 'type1'
    else:
        devicetypeerror = (
            'No device type selected: {}. Type 1 selected'.format(ip))
        print(devicetypeerror)
        devicetype = 'type1'
        error.append('''This device could generate some errors if configuration
is applied. This could include 6500 type devices.''')
        error.append(devicetypeerror)
        print ('Errors:')
        for x in error:
            print (x)


def glconf(cfgdiffs, **kwargs):
    # This includes the global configuration changes required.
    #
    d1 = {}  # Include what should be in the configuration.
    d2 = {}  # Include the answers of the parse.
    #
    i = 0
    cfg = '''
service tcp-keepalives-in
service tcp-keepalives-out
service password-encryption
service sequence-numbers
service counters max age 5
no service pad
no ip http server
no ip http secure-server
clock timezone CET 1
clock summer-time CEST recurring last Sun Mar 2:00 last Sun Oct 3:00
service timestamps debug datetime localtime show-timezone
service timestamps log datetime localtime
ip domain-name nms.local
no ip domain-lookup
ip ssh time-out 90
ip scp server enable
spanning-tree portfast bpduguard default
udld aggressive
errdisable recovery cause psecure-violation
errdisable recovery cause dtp-flap
errdisable recovery cause udld
errdisable recovery cause dhcp-rate-limit
errdisable recovery cause link-flap
snmp-server contact <customer contact>
snmp-server enable traps
ntp server 10.10.10.1
ntp server 10.10.20.1
'''
# Depending on platform
# vlan internal allocation policy ascending
    # a special line added with the hostname variable
    if swhostname:
        cfg = cfg + 'snmp-server chassis-id {}\n'.format(swhostname)
        # print ('cfg: ', cfg)
    #
    if devicetype == 'type1':
        cfg = cfg + '''
port-channel load-balance src-dst-ip
exception memory ignore overflow io
exception memory ignore overflow processor
no setup express
no vstack'''
    #
    elif devicetype == 'type2':
        cfg = cfg + '''
port-channel load-balance src-dst-ip
exception crashinfo maximum-files 5
no setup express
no vstack'''
    #
    elif devicetype == 'type3':
        cfg = cfg + '''
exception crashinfo maximum-files 5'''
    #
    # Puts the cfg text into a dict.
    for x in cfg.split('\n'):
        if x:
            key1 = 'gl' + str(i)
            d1[key1] = x
            i += 1
    #
    # Loop through d1 to check and add.
    for x in d1.keys():
        d2[x] = parse.find_objects(d1[x])
        if not d2[x]:
            cfgdiffs.append_line(d1[x].strip('^$'))
            # print (d1[x].strip('^$'))

    # Remove part, add commands to d3 that you wish to check and remove
    d3 = {}  # Include what should NOT be in the configuration.
    d4 = {}  # Include the answers of the parse.

    # Things that shouldn't be in the configuration.
    d3['gl0'] = '^errdisable recovery cause pagp-flap$'
    d3['gl1'] = '^errdisable recovery interval'
    d3['gl2'] = '^no cdp run$'
    d3['gl3'] = '^snmp-server system-shutdown$'

    # Loop through d3 to check and remove.
    for x in d3.keys():
        d4[x] = parse.find_objects(d3[x])
        if not d4[x]:
            del d4[x]

    if d4:
        cfgdiffs.append_line('!')
        for x in d4:
            if d3[x].startswith('no '):
                cfgdiffs.append_line(d3[x].strip('^$').replace('no ', ''))
            else:
                cfgdiffs.append_line('no ' + d3[x].strip('^$'))
        # cfgdiffs.append_line('no ' + d3[x].strip('^$'))
        # print (d1[x].strip('^$'))

    cfgdiffs.commit()
    return cfgdiffs


def unusedint(cfgdiffs, **kwargs):
    # Make changes to all unused interfaces.
    d1, d3, d5, d7 = {}, {}, {}, {}
    d2, d4, d6, d8 = {}, {}, {}, {}
    #
    for intf in unused_intfs:
        if (intf.text.split(' ')[1] == 'FastEthernet0') or (
           intf.text.split(' ')[1] == 'FastEthernet1'):
            continue

        d1['desc'] = 'description <<< UNUSED >>>'
        d1['maccess'] = 'switchport mode access'
        d1['shut'] = 'shutdown'
        #
        d3['access'] = 'switchport port-security'
        d3['log'] = 'logging'
        d3['power'] = 'power'
        d3['snmp'] = 'snmp'
        d3['storm'] = 'storm'
        d3['cdp'] = 'cdp'
        d3['spanning'] = 'spanning-tree'
        #
        d5['log'] = '^ no logging event power-inline-status'
        d5['log1'] = '^ no logging event link-status'
        #
        d7['ip'] = 'no ip address'
        #
        for x in d1.keys():
            d2[x] = intf.re_search_children(d1[x])
            if d2[x]:
                del d2[x]

        for x in d3.keys():
            d4[x] = intf.re_search_children(d3[x])
            if not d4[x]:
                del d4[x]

        for x in d5.keys():
            d6[x] = intf.re_search_children(d5[x])
            if not d6[x]:
                del d6[x]

        for x in d7.keys():
            d8[x] = intf.re_search_children(d7[x])
            if not d8[x]:
                del d8[x]

        if d4 or d2:
            cfgdiffs.append_line('!')
            # print('!')
            cfgdiffs.append_line('default ' + intf.text)
            cfgdiffs.append_line(intf.text)
            cfgdiffs.append_line(' description <<< UNUSED >>>')
            cfgdiffs.append_line(' shutdown')
            # special cases
            for x in d6:
                if d5[x].strip('^$').startswith(' no '):
                    cfgdiffs.append_line(d5[x].strip('^$').replace(
                        ' no', ''))
                else:
                    cfgdiffs.append_line(' no' + d3[x].strip('^$'))
            if d8:
                cfgdiffs.append_line('switchport')
            cfgdiffs.append_line(' switchport mode access')

    cfgdiffs.commit()
    return cfgdiffs


def glint(cfgdiffs, **kwargs):
    # Make general changes to all interfaces

    for intf in phys_intfs:
        d3, d5 = {}, {}
        #
        if kwargs['intrusive'] == 'yes':
            d3['speed'] = '^ speed auto 10 100'
            d3['mdix'] = '^ no mdix auto'
        d3['power'] = '^ power inline never'
        d3['udld'] = '^ udld port aggressive'
        d3['bpdu'] = '^ spanning-tree bpduguard enable'
        d3['powerlog'] = '^ no logging event power-inline-status'
        if devicetype == 'type2':
            d3['qos'] = '^ auto qos trust dscp'
        if devicetype == 'type3':
            d3['qos'] = '^ auto qos trust'
        #
        cfgdiffs = addremoveintf(cfgdiffs, intf, d3=d3, d5=d5)
    return cfgdiffs


def office(cfgdiffs, **kwargs):
    '''This includes everything related to the user interfaces. Including the
general commands'''
    # Global configuration checks
    if devicetype == 'type1':
        d1 = {}  # Include what should be in the configuration.
        d2 = {}  # Include the answers of the parse.
        #
        d1['mls'] = '^mls qos$'
        d1['mlsmap'] = '^mls qos map policed-dscp  10 18 24 26 46 to 8$'
        for x in d1.keys():
            d2[x] = parse.find_objects(d1[x])
            if not d2[x]:
                cfgdiffs.append_line(d1[x].strip('^$'))

        # This is repetetive code.
        d1sub = {}
        d1 = '^ip access-list extended Acl-Bulk-Data$'
        d1sub['acl1sub1'] = 'permit tcp any any eq 22'
        d1sub['acl1sub2'] = 'permit tcp any any eq 465'
        d1sub['acl1sub3'] = 'permit tcp any any eq 143'
        d1sub['acl1sub4'] = 'permit tcp any any eq 993'
        d1sub['acl1sub5'] = 'permit tcp any any eq 995'
        d1sub['acl1sub6'] = 'permit tcp any any eq 1914'
        d1sub['acl1sub7'] = 'permit tcp any any eq ftp'
        d1sub['acl1sub8'] = 'permit tcp any any eq ftp-data'
        d1sub['acl1sub9'] = 'permit tcp any any eq smtp'
        d1sub['acl1sub10'] = 'permit tcp any any eq pop3'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        # This is repetetive code.
        d1sub = {}
        d1 = '^ip access-list extended Acl-Default$'
        d1sub['acl1sub1'] = 'permit ip any any'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        # This is repetetive code.
        d1sub = {}
        d1 = '^ip access-list extended Acl-MultiEnhanced-Conf$'
        d1sub['acl1sub1'] = 'permit udp any any range 16384 32767'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        # This is repetetive code.
        d1sub = {}
        d1 = '^ip access-list extended Acl-Scavanger$'
        d1sub['acl1sub1'] = 'permit tcp any any range 2300 2400'
        d1sub['acl1sub2'] = 'permit udp any any range 2300 2400'
        d1sub['acl1sub3'] = 'permit tcp any any range 6881 6999'
        d1sub['acl1sub4'] = 'permit tcp any any range 28800 29100'
        d1sub['acl1sub5'] = 'permit tcp any any eq 1214'
        d1sub['acl1sub6'] = 'permit udp any any eq 1214'
        d1sub['acl1sub7'] = 'permit tcp any any eq 3689'
        d1sub['acl1sub8'] = 'permit udp any any eq 3689'
        d1sub['acl1sub9'] = 'permit tcp any any eq 11999'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        # This is repetetive code.
        d1sub = {}
        d1 = '^ip access-list extended Acl-Signaling$'
        d1sub['acl1sub1'] = 'permit tcp any any range 2000 2002'
        d1sub['acl1sub2'] = 'permit tcp any any range 5060 5061'
        d1sub['acl1sub3'] = 'permit udp any any range 5060 5061'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        # This is repetetive code.
        d1sub = {}
        d1 = '^ip access-list extended Acl-Transactional-Data$'
        d1sub['acl1sub1'] = 'permit tcp any any eq 443'
        d1sub['acl1sub2'] = 'permit tcp any any eq 1521'
        d1sub['acl1sub3'] = 'permit udp any any eq 1521'
        d1sub['acl1sub4'] = 'permit tcp any any eq 1526'
        d1sub['acl1sub5'] = 'permit udp any any eq 1526'
        d1sub['acl1sub6'] = 'permit tcp any any eq 1575'
        d1sub['acl1sub7'] = 'permit udp any any eq 1575'
        d1sub['acl1sub8'] = 'permit tcp any any eq 1630'
        d1sub['acl1sub9'] = 'permit udp any any eq 1630'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        # This is repetetive code.
        d1sub = {}
        d1 = '^class-map match-any Bulk-Data-Class$'
        d1sub['cmsub1'] = 'match access-group name Acl-Bulk-Data'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        d1 = '^class-map match-any Multimedia-Conf-Class$'
        d1sub['cmsub1'] = 'match access-group name Acl-MultiEnhanced-Conf'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        d1 = '^class-map match-any Voip-Data-Class$'
        d1sub['cmsub1'] = 'match ip dscp ef'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        d1 = '^class-map match-any Voip-Signal-Class$'
        d1sub['cmsub1'] = 'match ip dscp cs3'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        d1 = '^class-map match-any Default-Class$'
        d1sub['cmsub1'] = 'match access-group name Acl-Default'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        d1 = '^class-map match-any Transaction-Class$'
        d1sub['cmsub1'] = 'match access-group name Acl-Transactional-Data'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        d1 = '^class-map match-any Scavanger-Class$'
        d1sub['cmsub1'] = 'match access-group name Acl-Scavanger'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        d1 = '^class-map match-any Signaling-Class$'
        d1sub['cmsub1'] = 'match access-group name Acl-Signaling'
        # calling module for the repetetive task
        cfgdiffs = parent_child_check(d1, d1sub, cfgdiffs)

        # Service-policy, simple check
        d1 = '^policy-map Input-Policy$'
        if not parse.find_objects(d1):
            cfgdiffs.append_line('''!
policy-map Input-Policy
 class Voip-Data-Class
  set dscp ef
   police 128000 8000 exceed-action policed-dscp-transmit
 class Voip-Signal-Class
  set dscp cs3
   police  32000  8000 exceed-action policed-dscp-transmit
 class Multimedia-Conf-Class
  set dscp af41
   police 5000000 8000 exceed-action drop
 class Bulk-Data-Class
  set dscp af11
   police 10000000 8000 exceed-action policed-dscp-transmit
 class Transaction-Class
  set dscp af21
   police 10000000 8000 exceed-action policed-dscp-transmit
 class Scavanger-Class
  set dscp cs1
   police 10000000 8000 exceed-action policed-dscp-transmit
 class Signaling-Class
  set dscp cs3
   police 32000 8000 exceed-action drop
 class Default-Class
  set dscp default
   police 10000000 8000 exceed-action policed-dscp-transmit
!''')
    # end of device type 1

    # Finding all face interfaces, vlans can be between! 2 and 9, so 2 till and
    # with 8.
    faceports = []
    for i in range(2, 9):
        facevlan = 'switchport access vlan ' + str(i) + '$'
        for obj in phys_intfs:
            if obj.re_search_children(facevlan):
                faceports.append(obj)

    for intf in faceports:
        d1, d3, d5 = {}, {}, {}
        #
        stormlevel = stormcontrol(intf)
        #
        d1['facedesc'] = '^ description FACE-Client'
        d1['voice'] = '^ switchport voice vlan 200'
        d1['port'] = '^ switchport port-security'
        d1['portmax3'] = '^ switchport port-security maximum 3'
        d1['portage1'] = '^ switchport port-security aging time 1'
        d1['portagein'] = '^ switchport port-security aging type inactivity'
        d1['portfast'] = '^ spanning-tree portfast'
        d1['snmp'] = '^ no snmp trap link-status'
        d1['stormbroad'] = '^ storm-control broadcast level ' + stormlevel
        if devicetype == 'type1':
            # type1
            d1['inputPol'] = '^ service-policy input Input-Policy'
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
        elif devicetype == 'type2':
            # type 2
            d1['qos3650'] = '^ auto qos voip cisco-softphone'
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
        #
        d3['cdp'] = '^ no cdp enable'
        d3['mls'] = '^ mls qos trust device cisco-phone'
        d3['qos'] = '^ auto qos voip trust'
        d3['qos1'] = '^ auto qos voip cisco-phone'
        d3['srr'] = '^ srr-queue bandwidth shape'
        d3['speed'] = '^ speed auto 10 100'
        # d3['pol'] = '^ service-policy input AutoQoS-Police-CiscoPhone'

        # Special treatment for logging event commands
        d5['llink'] = '^ no logging event link-status'

        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1, d3=d3, d5=d5)
    cfgdiffs.commit()
    return cfgdiffs


def swtrunkpo(cfgdiffs, **kwargs):
    # Select all trunks that have a relation with a port-channel.
    hostname1 = 'description SW[0-9]+'
    # hostname2 = 'description [A-Z]{5}[0-9]{2}-.-..[0-9]{3}'
    hostname2 = 'description [A-Z]{5}[0-9]{2}-[IO]-[A-Z]{2}[0-9]{3}'

    # Verifying Port-channel virtual interfaces, a list is created based on
    # Port-channel
    # switchport mode trunk
    # and the hostname, legacy or current standard
    po_intf = []
    for obj in parse.find_objects('^interface Port-channel'):
        if (obj.re_search_children('switchport mode trunk') and (
                obj.re_search_children(hostname1) or
                obj.re_search_children(hostname2))):
                po_intf.append(obj)
    #
    for intf in po_intf:
        d1 = {}
        ponumber = intf.text.split('channel')[1]
        # Get the related physical interface
        posub = []
        # po_phys_intfs
        # posub = [obj for obj in phys_intfs \
        posub = [obj for obj in po_phys_intfs
                 if obj.re_search_children('channel-group ' + ponumber)]
        # if a interface match is returned, do the following:
        if posub:
            stormlevel = stormcontrol(intf)
            #
            d1['log2'] = '^ logging event trunk-status'
            d1['storm1'] = '^ storm-control broadcast level ' + stormlevel
            #
            if kwargs['intrusive'] == 'yes':
                d1['nonegotiate'] = '^ switchport nonegotiate'
            #
            if devicetype == 'type1':
                d1['log3'] = '^ logging event status'
                d1['log4'] = '^ logging event bundle-status'
                d1['storm2'] = '^ storm-control multicast level ' + stormlevel
            elif devicetype == 'type2':
                d1['log3'] = '^ logging event status'
                d1['log4'] = '^ logging event bundle-status'
                d1['storm2'] = '^ storm-control multicast level ' + stormlevel
                d1['log1'] = '^ logging event link-status'
            elif devicetype == 'type3':
                d1['log1'] = '^ logging event link-status'
    #
            cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1)

        elif kwargs['intrusive'] == 'yes':
            # no interface was returned. The port-channel can be removed.
            cfgdiffs.append_line('!\n!\n!!!!! SWTRUNK: Port-channel can be \
removed, not used.')
            cfgdiffs.append_line('no ' + intf.text)
            cfgdiffs.append_line('!')

        # Port-channel part has finised
    #
    # Creating a list of all physical interfaces, belonging to the same
    # port-channels. Based on the same criteria.
    # Applying the specific configurations.
    trunk_intf = []
    for obj in po_phys_intfs:
        if (obj.re_search_children('switchport mode trunk') and (
                obj.re_search_children(hostname1) or
                obj.re_search_children(hostname2))):
            trunk_intf.append(obj)
    #
    for intf in trunk_intf:
        d1 = {}
        d1['ltrunk'] = '^ logging event trunk-status'
        if devicetype == 'type1':
            d1['lstat'] = '^ logging event status'
            d1['mls'] = '^ mls qos trust dscp'
            d1['lbundle'] = '^ logging event bundle-status'
        elif devicetype == 'type2':
            d1['log1'] = '^ logging event link-status'
            d1['lstat'] = '^ logging event status'
            d1['lbundle'] = '^ logging event bundle-status'
        elif devicetype == 'type3':
            d1['log1'] = '^ logging event link-status'
    #
        # print ('intf:', intf )
        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1)
    cfgdiffs.commit()
    return cfgdiffs


def swtrunk(cfgdiffs, **kwargs):
    # Select all trunks from the physical interfaces, That don't have a
    # relation with a port-channel.
    hostname1 = 'description SW[0-9]+'
    # hostname2 = 'description [A-Z]{5}[0-9]{2}-.-..[0-9]{3}'
    hostname2 = 'description [A-Z]{5}[0-9]{2}-[IO]-[A-Z]{2}[0-9]{3}'
    #
    # Creating a list of all physical interfaces, that are trunk
    trunk_intf = []
    for obj in phys_intfs:
        if (obj.re_search_children('switchport mode trunk') and (
                obj.re_search_children(hostname1) or
                obj.re_search_children(hostname2))):
            trunk_intf.append(obj)
    #
    for intf in trunk_intf:
        stormlevel = stormcontrol(intf)
        d1 = {}
        d1['ltrunk'] = '^ logging event trunk-status'
        d1['storm1'] = '^ storm-control broadcast level ' + stormlevel
        if kwargs['intrusive'] == 'yes':
            d1['nonegotiate'] = '^ switchport nonegotiate'
        if devicetype == 'type1':
            d1['lstat'] = '^ logging event status'
            d1['mls'] = '^ mls qos trust dscp'
            d1['lbundle'] = '^ logging event bundle-status'
            d1['storm2'] = '^ storm-control multicast level ' + stormlevel
        elif devicetype == 'type2':
            d1['log1'] = '^ logging event link-status'
            d1['lstat'] = '^ logging event status'
            d1['lbundle'] = '^ logging event bundle-status'
            d1['storm2'] = '^ storm-control multicast level ' + stormlevel
        elif devicetype == 'type3':
            d1['log1'] = '^ logging event link-status'
        # print ('intf:', intf )
        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1)
    cfgdiffs.commit()
    return cfgdiffs


def wlctrunk(cfgdiffs, **kwargs):
    # Select all trunks from the physical interfaces, which indicate a trunk
    # connection to another switch.
    hostname1 = 'description WLC[0-9]+'
    hostname2 = 'description [A-Z]{5}[0-9]{2}-WLC[0-9]{2}'
    hostname3 = 'description [A-Z]{5}[0-9]{2}-[IO]-CW[0-9]{3}'
    #
    # Verifying Port-channel virtual interfaces, a list is created based on
    # Port-channel
    # switchport mode trunk
    # and the hostname, legacy or current standard
    po_intf = []
    for obj in parse.find_objects('^interface Port-channel'):
        if (obj.re_search_children('switchport mode trunk') and (
                obj.re_search_children(hostname1) or
                obj.re_search_children(hostname2) or
                obj.re_search_children(hostname3) or
                obj.re_search_children('WLC') or
                obj.re_search_children('wlc'))):
            po_intf.append(obj)
    #
    for intf in po_intf:
        d1 = {}
        ponumber = intf.text.split('channel')[1]
        # Get the related physical interface
        posub = []
        posub = [obj for obj in po_phys_intfs
                 if obj.re_search_children('channel-group ' + ponumber)]
        # if a Port-channel is returned, do the following:
        if posub:
            stormlevel = stormcontrol(intf)
            d1['log2'] = '^ logging event trunk-status'
            d1['storm1'] = '^ storm-control broadcast level ' + stormlevel
            d1['stp'] = '^ spanning-tree portfast trunk'
            if kwargs['intrusive'] == 'yes':
                d1['nonegotiate'] = '^ switchport nonegotiate'
            if devicetype == 'type1':
                d1['log3'] = '^ logging event status'
                d1['log4'] = '^ logging event bundle-status'
                d1['storm2'] = '^ storm-control multicast level ' + stormlevel
            elif devicetype == 'type2':
                d1['log1'] = '^ logging event link-status'
                d1['log3'] = '^ logging event status'
                d1['log4'] = '^ logging event bundle-status'
                d1['storm2'] = '^ storm-control multicast level ' + stormlevel
            elif devicetype == 'type3':
                d1['log1'] = '^ logging event link-status'
            #
            cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1)
    #
    # Else, no ports belong to this port-channel and it could be removed.
        elif kwargs['intrusive'] == 'yes':
            # no interface was returned. The port-channel can be removed.
            cfgdiffs.append_line('!\n!\n!!!! WLCTRUNK: Port-channel can \
be removed, not used.')
            cfgdiffs.append_line('no ' + intf.text)
            cfgdiffs.append_line('!')
    #
    # Select all interfaces from the physical interfaces, which belong to the
    # port-channels, using the same criteria.
    trunk_intf = []
    for obj in po_phys_intfs:
        if (obj.re_search_children('switchport mode trunk') and (
                obj.re_search_children(hostname1) or
                obj.re_search_children(hostname2) or
                obj.re_search_children(hostname3))):
            trunk_intf.append(obj)
    #
    for intf in trunk_intf:
        d1 = {}
        # d1['vlan1'] = 'switchport trunk allowed vlan 20-24,250,901'
        # d1['llinkstat'] = 'logging event link-status'
        d1['ltrunk'] = '^ logging event trunk-status'
        if devicetype == 'type1':
            d1['lstat'] = '^ logging event status'
            d1['mls'] = '^ mls qos trust dscp'
        elif devicetype == 'type2':
            d1['lstat'] = '^ logging event status'
            d1['log1'] = '^ logging event link-status'
        elif devicetype == 'type3':
            d1['log1'] = '^ logging event link-status'
    #
        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1)
    cfgdiffs.commit()
    return cfgdiffs


def dedvoice(cfgdiffs, **kwargs):
    # Making a list of dedicated voiceports
    voiceports = []
    for obj in phys_intfs:
        if obj.re_search_children('switchport access vlan 200$'):
            voiceports.append(obj)
    #
    # Create the policy-map if it doesn't exists
    if voiceports:
        if not parse.find_objects('policy-map Voice-EF'):
            cfgdiffs.append_line('!')
            cfgdiffs.append_line('policy-map Voice-EF')
            cfgdiffs.append_line(' class class-default')
            cfgdiffs.append_line('  set dscp ef')
    #
    for intf in voiceports:
        d1, d5 = {}, {}
        stormlevel = stormcontrol(intf)
        d1['facedesc'] = '^ description VOICE'
        d1['access'] = '^ switchport mode access'
        d1['port'] = '^ switchport port-security'
        d1['portmax3'] = '^ switchport port-security maximum 3'
        d1['portage1'] = '^ switchport port-security aging time 1'
        d1['portagein'] = '^ switchport port-security aging type inactivity'
        d1['portfast'] = '^ spanning-tree portfast'
        d1['snmp'] = '^ no snmp trap link-status'
        d1['stormbroad'] = '^ storm-control broadcast level ' + stormlevel
        # d1['cdp'] = 'no cdp enable'
        d1['Pol'] = '^ service-policy input Voice-EF'
    #
        if devicetype == 'type1':
            # type1
            d1['mlsdscp'] = '^ mls qos trust dscp'
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
        elif devicetype == 'type2':
            # type 2
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
    #
        d5['llink'] = '^ no logging event link-status'
    #
        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1, d5=d5)
    #
    cfgdiffs.commit()
    return cfgdiffs


def dedvideo(cfgdiffs, **kwargs):
    # Making a list of dedicated video ports
    videoports = []
    for obj in phys_intfs:
        if obj.re_search_children('switchport access vlan 225$'):
            videoports.append(obj)
    #
    # Create the policy-map if it doesn't exists
    if videoports:
        if not parse.find_objects('policy-map Video-AF41'):
            cfgdiffs.append_line('policy-map Video-AF41')
            cfgdiffs.append_line(' class class-default')
            cfgdiffs.append_line('  set dscp af41')
    #
    for intf in videoports:
        d1, d5 = {}, {}
        stormlevel = stormcontrol(intf)
        d1['desc'] = '^ description Telepresence VC'
        d1['access'] = '^ switchport mode access'
        d1['port'] = '^ switchport port-security'
        d1['portmax3'] = '^ switchport port-security maximum 3'
        d1['portage1'] = '^ switchport port-security aging time 1'
        d1['portagein'] = '^ switchport port-security aging type inactivity'
        d1['portfast'] = '^ spanning-tree portfast'
        d1['snmp'] = '^ no snmp trap link-status'
        d1['stormbroad'] = '^ storm-control broadcast level ' + stormlevel
        d1['cdp'] = '^ no cdp enable'
        d1['Pol'] = '^ service-policy input Video-AF41'
        if devicetype == 'type1':
            # type1
            d1['mlsdscp'] = '^ mls qos trust dscp'
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
        elif devicetype == 'type2':
            # type 2
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
    #
        d5['llink'] = '^ no logging event link-status'
    #
        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1, d5=d5)
    cfgdiffs.commit()
    return cfgdiffs


def l3vlan(cfgdiffs, **kwargs):
    d2, d4 = {}, {}
    for intf in l3vlan_intfs:
        d1, d3, = {}, {}
        # Specific entry for VLAN 1. It should not be enabled.
        if intf.text.split(' ')[1] == 'Vlan1':
            if kwargs['intrusive'] == 'yes':
                d1['vl1'] = ' description <<< UNUSED >>>'
                d1['vl2'] = ' no ip address'
                d1['vl3'] = ' shutdown'
    #
                d3['vl1'] = 'vrf forwarding'
                d3['vl2'] = 'ip helper-address'
                d3['vl3'] = 'no ip redirects'
                d3['vl4'] = 'no ip proxy-arp'
                d3['vl5'] = 'no ip route-cache'
    #
                for x in d1.keys():
                    d2[x] = intf.re_search_children(d1[x])
                    if d2[x]:
                        del d2[x]
                for x in d3.keys():
                    d4[x] = intf.re_search_children(d3[x])
                    if not d4[x]:
                        del d4[x]
    #
                if d4 or d2:
                    cfgdiffs.append_line('!')
                    # print('!')
                    cfgdiffs.append_line('default ' + intf.text)
                    cfgdiffs.append_line(intf.text)
                    cfgdiffs.append_line(' description <<< UNUSED >>>')
                    cfgdiffs.append_line(' no ip address')
                    cfgdiffs.append_line(' shutdown')
    #
        # If the vlan doesn't have an IP address, it shouldn't exists as an SVI.
        elif (intf.re_search_children(' no ip address') and
              kwargs['intrusive'] == 'yes'):
            cfgdiffs.append_line('!')
            cfgdiffs.append_line('!!!! L3VLAN  This interface doesn\'t have \
an ip address. Not SVI worthy.')
            cfgdiffs.append_line('no {}'.format(intf.text))
        # Other VLANs are checked below.
        else:
            d1['vl1'] = '^ no ip redirects$'
            d1['vl2'] = '^ no ip proxy-arp$'
    #
            d3['vl1'] = '^ ip helper-address global'
            # Special
            iprc = []
            iprc = intf.re_search_children('^ no ip route-cache')
    #
            cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1, d3=d3, iprc=iprc)
    cfgdiffs.commit()
    return cfgdiffs


def waas(cfgdiffs, **kwargs):
    # Verifying the WAAS configuration. It will create a list based on vlan 202
    # and access port.
    waasports = []
    waasvlan = 'switchport access vlan 202$'
    access = 'switchport mode access$'
    for obj in phys_intfs:
        if (obj.re_search_children(waasvlan) and
                obj.re_search_children(access)):
            waasports.append(obj)
    #
    for intf in waasports:
        d1, d3, d5 = {}, {}, {}
        stormlevel = stormcontrol(intf)
        d1['port'] = '^ switchport port-security'
        d1['portmax3'] = '^ switchport port-security maximum 3'
        d1['portage1'] = '^ switchport port-security aging time 1'
        d1['portagein'] = '^ switchport port-security aging type inactivity'
        d1['portfast'] = '^ spanning-tree portfast'
        d1['stormbroad'] = '^ storm-control broadcast level ' + stormlevel
        #
        if devicetype == 'type1':
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
            d1['log1'] = '^ logging event status'
        elif devicetype == 'type2':
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
            d1['log1'] = '^ logging event status'
        elif devicetype == 'type3':
            d1['log1'] = '^ logging event link-status'
        #
        # Things that shouldn't be in the configuration.
        d3['cdp'] = '^ no cdp enable'
        d3['snmp'] = '^ no snmp trap link-status'
    #
        # Special treatment for logging event commands
        d5['llink'] = '^ no logging event link-status'
        #
        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1, d3=d3, d5=d5)
    cfgdiffs.commit()
    return cfgdiffs


def wan(cfgdiffs, **kwargs):
    # This part is to verify the WAN port, only if it is an access port.
    wanaccports = []
    wanvlan = 'switchport access vlan 201$'
    access = 'switchport mode access$'
    for obj in phys_intfs:
        if (obj.re_search_children(wanvlan) and
                obj.re_search_children(access)):
            wanaccports.append(obj)
    #
    # print ('WAN access:', wanaccports)
    # print ('devicetype:', devicetype)
    #
    for intf in wanaccports:
        d1, d3, d5 = {}, {}, {}
        stormlevel = stormcontrol(intf)
        d1['portfast'] = '^ spanning-tree portfast'
        d1['stormbroad'] = '^ storm-control broadcast level ' + stormlevel
        #
        if devicetype == 'type1':
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
            d1['log1'] = '^ logging event status'
            d1['qos'] = '^ mls qos trust dscp'
        elif devicetype == 'type2':
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
            d1['log1'] = '^ logging event status'
            d1['log1'] = '^ logging event link-status'
        elif devicetype == 'type3':
            d1['log1'] = '^ logging event link-status'
        # Things that shouldn't be in the configuration.
        d3['cdp'] = '^ no cdp enable'
        d3['snmp'] = '^ no snmp trap link-status'
        # Special treatment for logging event commands
        d5['llink'] = '^ no logging event link-status'
        #
        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1, d3=d3, d5=d5)
    cfgdiffs.commit()
    return cfgdiffs


def wantrunk(cfgdiffs, **kwargs):
    # This part checks the WAN port if it is a trunk, usually together with WAAS
    # It will only be considered if it has an allowed vlan list
    wantrunkports = []
    wantrunk = 'switchport trunk allowed vlan.*201'
    trunk = 'switchport mode trunk$'
    for obj in phys_intfs:
        if (obj.re_search_children(wantrunk) and
                obj.re_search_children(trunk)):
            wantrunkports.append(obj)
    #
    # print ('WAN trunk:', wantrunkports)
    # print ('devicetype:', devicetype)
    #
    for intf in wantrunkports:
        d1, d3, d5 = {}, {}, {}
        stormlevel = stormcontrol(intf)
        d1['stormbroad'] = '^ storm-control broadcast level ' + stormlevel
        d1['logt'] = '^ logging event trunk-status'
        if kwargs['intrusive'] == 'yes':
            d1['nonegotiate'] = '^ switchport nonegotiate'
        #
        if devicetype == 'type1':
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
            d1['log1'] = '^ logging event status'
            d1['qos'] = '^ mls qos trust dscp'
        elif devicetype == 'type2':
            d1['stormmulti'] = '^ storm-control multicast level ' + stormlevel
            d1['log1'] = '^ logging event status'
            d1['log1'] = '^ logging event link-status'
        elif devicetype == 'type3':
            d1['log1'] = '^ logging event link-status'
        # Things that shouldn't be in the configuration.
        d3['cdp'] = '^ no cdp enable'
        d3['snmp'] = '^ no snmp trap link-status'
        d3['bpdu'] = '^ spanning-tree bpduguard'
        d3['portfast'] = '^ spanning-tree portfast trunk'
        # Special treatment for logging event commands
        d5['llink'] = '^ no logging event link-status'
        #
        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1, d3=d3, d5=d5)
    cfgdiffs.commit()
    return cfgdiffs


def fwfailover(cfgdiffs, **kwargs):
    # FW failover ports
    fwfail = []
    fwvlan = 'switchport access vlan 210$'
    access = 'switchport mode access$'
    for obj in phys_intfs:
        if (obj.re_search_children(fwvlan) and
                obj.re_search_children(access)):
            fwfail.append(obj)
    #
    # print ('WAN access:', wanaccports)
    # print ('devicetype:', devicetype)

    for intf in fwfail:
        d1, d3, d5 = {}, {}, {}
        stormlevel = stormcontrol(intf)
        d1['portfast'] = '^ spanning-tree portfast'
        d1['cdp'] = '^ no cdp enable'
        #
        # Things that shouldn't be in the configuration.
        d3['snmp'] = '^ no snmp trap link-status'
        d3['stormbroad'] = '^ storm-control broadcast level ' + stormlevel
        if devicetype == 'type1':
            d3['qos'] = '^ mls qos trust dscp'
            d3['stormmulti'] = '^ storm-control multicast level ' + stormlevel
        elif devicetype == 'type2':
            d3['stormmulti'] = '^ storm-control multicast level ' + stormlevel
        # Special treatment for logging event commands
        d5['llink'] = '^ no logging event link-status'
        #
        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1, d3=d3, d5=d5)
    cfgdiffs.commit()
    return cfgdiffs


def fwpc(cfgdiffs, **kwargs):
    # FW port-channels
    po_fw_intf = []
    for obj in parse.find_objects('^interface Port-channel'):
        if (obj.re_search_children('switchport mode trunk') and (
                obj.re_search_children('description FW'))):
            po_fw_intf.append(obj)
    # print ('PO FW intf:', po_fw_intf)
    #
    for intf in po_fw_intf:
        d1, d3, d5 = {}, {}, {}
        ponumber = intf.text.split('channel')[1]
        # Get the related physical interface, first empty the list
        posub = []
        posub = [obj for obj in po_phys_intfs
                 if obj.re_search_children('channel-group ' + ponumber)]
        # if a interface match is returned, do the following:
        if posub:
            d1['portfast'] = '^ spanning-tree portfast trunk'
            if kwargs['intrusive'] == 'yes':
                d1['noneg'] = '^ switchport nonegotiate'
            #
            # Things that shouldn't be in the configuration.
            d3['snmp'] = '^ no snmp trap link-status'
            d3['stormbroad'] = '^ storm-control broadcast level'
            # d3['lpower'] = '^ no logging event power-inline-status'
            if devicetype == 'type1':
                d3['stormmulti'] = '^ storm-control multicast level'
            elif devicetype == 'type2':
                d3['stormmulti'] = '^ storm-control multicast level'

            # Special treatment for logging event commands
            d5['llink'] = '^ no logging event link-status'
            #
            cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1, d3=d3, d5=d5)
            #
        elif kwargs['intrusive'] == 'yes':
            # no interface was returned. The port-channel can be removed.
            cfgdiffs.append_line('!\n!\n!!!!! FW TRUNK: Port-channel can be \
removed, not used.')
            cfgdiffs.append_line('no ' + intf.text)
            cfgdiffs.append_line('!')
    #
    # Also verifying the physical ports, related to the port-channels.
    trunk_intf = []
    for obj in po_phys_intfs:
        if (obj.re_search_children('switchport mode trunk') and (
                obj.re_search_children('description FW'))):
            trunk_intf.append(obj)
    # print ('FW trunk intf:', trunk_intf)

    for intf in trunk_intf:
        d1 = {}
        d1['cdp'] = '^ no cdp enable'
        if devicetype == 'type1':
            d1['mls'] = '^ mls qos trust dscp'
    #
        cfgdiffs = addremoveintf(cfgdiffs, intf, d1=d1)
    cfgdiffs.commit()
    return cfgdiffs

