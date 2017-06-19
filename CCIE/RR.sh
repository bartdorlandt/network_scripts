#!/bin/bash
echo "What is your password?"
read PASS
export PASS
echo "What is your username?"
read USERNAME
export USERNAME

export HOST=racks.ccierackrentals.com
# Using backup since it is faster
#export HOST=backup.ccierackrentals.com

echo "What is the rack number, I expect 2 digits."
read RACKNUMBER

export FULLRACKNUMBER=23$RACKNUMBER
if [ "$FULLRACKNUMBER" == "2332" ] ; then
 export FULLRACKNUMBER=2330
fi

# if one session is lost, open a new virt. window (F2) and do 
# log in with the password, after this you could rename the window with F8.
# access issues: http://www.ccierackrentals.com/setup-guide/telnet-access

# Start a new session with the name RR
byobu new-session -d -s RR; 
# Add a bunch of 'tabs' with corresponding names
byobu new-window -t RR:1 -n 'R1' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS r1'; 
byobu new-window -t RR:2 -n 'R2' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS r2';
byobu new-window -t RR:3 -n 'R3' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS r3';
byobu new-window -t RR:4 -n 'R4' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS r4';
byobu new-window -t RR:5 -n 'R5' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS r5';
byobu new-window -t RR:6 -n 'SW1' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS sw1';
byobu new-window -t RR:7 -n 'SW2' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS sw2';
byobu new-window -t RR:8 -n 'SW3' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS sw3';
byobu new-window -t RR:9 -n 'SW4' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS sw4';
byobu new-window -t RR:10 -n 'BB1' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS BB1';
byobu new-window -t RR:11 -n 'BB2' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS BB2';
byobu new-window -t RR:12 -n 'BB3' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS BB3';
#byobu new-window -t RR:13 -n 'MAIN' './RR_expect.sh $HOST $FULLRACKNUMBER $USERNAME $PASS hoi';
# Select the window where you want to start
byobu select-window -t RR:0; 
# Start byobu with the RR session with 256 colors (man tmux)
byobu -2 attach-session -t RR

