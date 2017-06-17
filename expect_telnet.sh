#!/usr/bin/expect -f
# Author: Bart Dorlandt, bdorlandt@legian.nl
# version 0.4, 2016-09-21
#   Added a check for an ip address even if the string is longer.
# version 0.3, 20160414
#   Added if for loop or interact action.
#   Added VzB part as well.
# version 0.2, 20160412
#   Not checking host keys and using an empty userknownhostfile.
# version 0.1, 2015-09-23

set timeout 10
set IPstring [lindex $argv 0]
set OUTPUT [lindex $argv 1]
set CMD [lindex $argv 2]
set LOOP [lindex $argv 3]
set Username "$env(ACSUSER)"
set Password "$env(ACSPASS)"
set VzB 0
set IPaddress 0

#
#if {! [regexp {(\d+\.\d+\.\d+\.\d+)} $IPaddress]} {
if { $IPstring == "" } {
  puts "\nNo IP address or hostname given. Exiting.\n"
  exit
}
# Verifying the string. Take only the IP address from it.
regexp {((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)} $IPstring IPaddress
# If empty, use the normal value. Poor mans next choice for a hostname.
if { "$IPaddress" == "0" } { set IPaddress $IPstring }

if {[info exists env(VZBUSER)]} { set vzbuser "$env(VZBUSER)" }
if {[info exists env(VZBPASS)]} { set vzbpass "$env(VZBPASS)" }
if {[info exists env(SSHLOG)]} { 
  set SSHLOG "$env(SSHLOG)"
  if {! "$env(SSHLOG)" == "no"} {
    set SSHLOG "yes"
  } 
} else {
  set SSHLOG "yes"
}
  
  #set SSHLOG "$env(SSHLOG)" } else { set SSHLOG "no" }
#set vzbtest "$env(VZBPASS2)"
#set Directory DIRECTORY_PATH

if {[file exists $CMD ]} {
  log_file -a $OUTPUT
  set f [open "$CMD"]
  set commands [split [read $f] "\n"]
  close $f
}

regexp {(10\.32\.\d+\.\d+)} $IPaddress VzB
set DATE [exec date +%Y%m%d_%H%M%S]
set YEAR [exec date +%Y]
set LOGDIR "$env(HOME)/sshlog/$YEAR"
if {! [file isdirectory $LOGDIR]} { file mkdir $LOGDIR }

if { $VzB == "0" } {
  if { "$SSHLOG" == "yes" } {
    spawn script -q -c "telnet $IPaddress" ${LOGDIR}/${IPaddress}_${DATE}.log
  } else {
#  #puts "vzb = $VzB"
    spawn telnet $IPaddress
  }
} else {
  spawn script -q -c "telnet $IPaddress" ${LOGDIR}/${IPaddress}_${DATE}.log
}

#log_file -a $Directory/session_$IPaddress.log
#send_log "### /START-TELNET-SESSION/ IP: $IPaddress @ [exec date] ###\r"

# Checking on several things, WLC, Switches, FW
expect {
  # WLC
  "User: " {
    send "$Username\r"
    expect "Password:"
    send "$Password\r"
    if { $LOOP == "loop" } {
      # the loop part is executed
      foreach cmd $commands {
        expect ">"
        send "$cmd\r"
      }
    } else {
      interact
    }
  }
  # Switches
  "ACS*sername:" {
    send "$Username\r"
    expect "ACS*assword:"
    send "$Password\r"
    #expect "\#" 
    if { $LOOP == "loop" } {
      #expect "\#" 
      # the loop part is executed
      foreach cmd $commands {
        # example legacy switch names
        #$prompt = /^SW[0-9]{4,6}/.'#';
        expect "\#"
        send "$cmd\r"
      }
    } else {
      interact
    }
  }
  # FW (legacy and new)
  "$Username@*assword:" {
    send "$Password\r"
    expect {
      "\#" {
        if { $LOOP == "loop" } {
          # the loop part is executed
          foreach cmd $commands {
            expect "\#"
            send "$cmd\r"
          }
        } else {
          interact
        }
      }
      "> " {
        send "enable\r"
        send "$Password\r"
        if { $LOOP == "loop" } {
          # the loop part is executed
          foreach cmd $commands {
            expect "\#"
            send "$cmd\r"
          }
        } else {
          interact
        }
      }
    }
  }
  "Connection refused" {
    puts "\nThis device doesn't support SSH.\n"
    puts "Copy the following text to try telnet."
    puts "\ntelnet $IPaddress"
    exit
  }
  Password: {
    send "$Password\r"
    expect {
      "\# " {
        if { $LOOP == "loop" } {
          # the loop part is executed
          foreach cmd $commands {
            expect "\#"
            send "$cmd\r"
          }
        } else {
          interact
        }
      }
      "Password:" {
        puts "\n\nIt seems TACACS+ isn't configured (correctly).\n\n"
        exit
      }
    }
  }
  "TACACS Username:" {
    if {[info exists env(VZBUSER)] && [info exists env(VZBPASS)]} {
      #puts "else vzb = $VzB"
      send "$vzbuser\r"
      expect "TACACS Password:"
      send "$vzbpass\r"
      interact
    } else {
      interact
    }
  }
  timeout {
    puts "\n\nTimeout reached.\nThe device didn't respond in time.\n\n"
   # puts "This doesn't seems to be a WLC, FW or Switch.\n\n";
  }
}
#interact
#send_log "\r### /END-TELNET-SESSION/ IP: $IPaddress @ [exec date] ###\r"
exit
