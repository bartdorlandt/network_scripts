#!/bin/sh
echo "What is your password?"
read PASS
export PASS
echo "what is the IP address?"
read HOST
export HOST

# if one session is lost, open a new virt. window (F2) and do 
# telnet 46.28.145.112 <port>
# log in with the password, after this you could rename the window with F8.

# Start a new session with the name C360
byobu new-session -d -s C360; 
# Add a bunch of 'tabs' with corresponding names
byobu new-window -t C360:1 -n 'R1' './C360_expect.sh $HOST 10037 $PASS'; 
byobu new-window -t C360:2 -n 'R2' './C360_expect.sh $HOST 10038 $PASS'; 
byobu new-window -t C360:3 -n 'R3' './C360_expect.sh $HOST 10039 $PASS'; 
byobu new-window -t C360:4 -n 'R4' './C360_expect.sh $HOST 10040 $PASS'; 
byobu new-window -t C360:5 -n 'R5' './C360_expect.sh $HOST 10041 $PASS'; 
byobu new-window -t C360:6 -n 'SW1' './C360_expect.sh $HOST 10046 $PASS'; 
byobu new-window -t C360:7 -n 'SW2' './C360_expect.sh $HOST 10047 $PASS'; 
byobu new-window -t C360:8 -n 'SW3' './C360_expect.sh $HOST 10048 $PASS'; 
byobu new-window -t C360:9 -n 'SW4' './C360_expect.sh $HOST 10049 $PASS'; 
byobu new-window -t C360:10 -n 'R7-FRS' './C360_expect.sh $HOST 10043 $PASS'; 
byobu new-window -t C360:11 -n 'R6' './C360_expect.sh $HOST 10042 $PASS'; 
# Select the window where you want to start
byobu select-window -t C360:0; 
# Start byobu with the C360 session with 256 colors (man tmux)
byobu -2 attach-session -t C360

