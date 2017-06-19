#!/usr/bin/expect
# Test expect script to telnet.

 #First argument , INE
set name [lindex $argv 0]
 #Second argument , Port
set port [lindex $argv 1]
 #3rd argument , Username
set username [lindex $argv 2]
 #4th argument , Password
set pass [lindex $argv 3]
 #5th argument , Device
set device [lindex $argv 4]

spawn telnet $name $port
sleep 3
expect "Username:"
send "$username\r"
sleep 1
expect "Password:"
send "$pass\r"

sleep 2
# Send a few enters
#send "\r"
#send "\r"

# Connect to the actual device:
send "$device\r"

 # This hands control of the keyboard over two you (Nice expect feature!)
interact

