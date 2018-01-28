#!/usr/bin/env python3
'''This script can be used to check AP's. A recent bug was found that could be verified
by checking the flash.

This script will query the WLC and extracts the AP's by their IP addresses. Next step is
to query those for their flash.
'''

# Example output
# =========================================================================================
# Id   Name                 Type               IPv4 address     Space(b)  Free(b)   Free(%)
# =========================================================================================
# 1    FT-MEP01-AP001       AIR-CAP3702I-E-K9  192.168.100.217  40900608  18628096  46
# 2    FT-MEP01-AP101       AIR-CAP3702I-E-K9  192.168.100.221  40900608  18855936  46
# 3    AP2602E              AIR-CAP2602E-E-K9  192.168.100.226  31739904  9910784   31
# =========================================================================================
# --- Processing the AP list took 18 seconds ---

import re
# import time
from netmiko import ConnectHandler


def percentage(part, whole):
    return round(100 * float(part)/float(whole))


# Credentials
connection_wlc = {
    "device_type": "cisco_wlc",
    "ip": "192.168.100.1",
    "username": "Cisco",
    "password": "Cisco",
}
connection_ap = {
    "device_type": "cisco_asa",
    "username": "AP",
    "password": "AP123",
    "secret": "AP123",
}
# Check for SKU "AIR-CAP" and correct IPv4 address and put them in groups
ipre = re.compile(r"^(.*?)\s+.*?(AIR-CAP.+?)\s+.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")

# Connect to the WLC to create AP list
device = ConnectHandler(**connection_wlc)
output = device.send_command("show ap summary")
# close the session
device.disconnect()

# Proces every line and put it in a list
aps = [ipre.search(line).groups() for line in output.split("\n") if ipre.search(line)]

# Connect to all of the APs in the array
print("="*88)
print("{:<4} {:<20} {:<18} {:<16} {:<9} {:<9} {:<2}".format(
    "Id", "Name", "Type", "IPv4 address", "Space(b)", "Free(b)", "Free(%)"))
print("="*88)

# start_time = time.time()
for num, ap in enumerate(aps):
    apname, apmodel, ip = ap
    device = ConnectHandler(ip=ip, **connection_ap)
    output = device.send_command("show file systems | i rw   flash:")
    # close the session
    device.disconnect()

    if "flash:" in output:
        _, size, free, _, _, _ = output.split()
    else:
        # In case no flash info is returned -> AP BROKEN?!
        size = free = "UNKNOWN!"

    print("{:<4} {:<20} {:<18} {:<16} {:<9} {:<9} {:<2}".format(
        num+1, apname, apmodel, ip, size, free, (percentage(free, size))))


# print("="*88)
# print("--- Processing the AP list took %s seconds ---" % round((time.time() - start_time)))
