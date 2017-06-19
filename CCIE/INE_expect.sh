#!/usr/bin/expect
# Test expect script to telnet.

 #First argument , INE
set name [lindex $argv 0]
 #Second argument , User
set user [lindex $argv 1]
 #3rd argument , Password
set pass [lindex $argv 2]
 #4th argument , Router name
#set device [lindex $argv 3]

spawn telnet $name
expect "Username:"
send "$user\r"
expect "Password:"
send "$pass\r"

sleep 2
# Send a few enters
send "\r"
send "\r"
#expect "AS>"
#send "$device\r"
sleep 1
# Send a few enters
send "\r"
send "\r"
 # This hands control of the keyboard over two you (Nice expect feature!)
interact

