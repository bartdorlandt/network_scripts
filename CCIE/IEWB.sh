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

# Start a new session with the name IEWB
byobu new-session -d -s IEWB; 
# Add a bunch of 'tabs' with corresponding names
byobu new-window -t IEWB:1 -n 'R1' './IEWB_expect.sh $HOST 10001 $PASS'; 
byobu new-window -t IEWB:2 -n 'R2' './IEWB_expect.sh $HOST 10002 $PASS'; 
byobu new-window -t IEWB:3 -n 'R3' './IEWB_expect.sh $HOST 10003 $PASS'; 
byobu new-window -t IEWB:4 -n 'R4' './IEWB_expect.sh $HOST 10004 $PASS'; 
byobu new-window -t IEWB:5 -n 'R5' './IEWB_expect.sh $HOST 10005 $PASS'; 
byobu new-window -t IEWB:6 -n 'R6' './IEWB_expect.sh $HOST 10006 $PASS'; 
byobu new-window -t IEWB:7 -n 'SW1' './IEWB_expect.sh $HOST 10010 $PASS'; 
byobu new-window -t IEWB:8 -n 'SW2' './IEWB_expect.sh $HOST 10011 $PASS'; 
byobu new-window -t IEWB:9 -n 'SW3' './IEWB_expect.sh $HOST 10012 $PASS'; 
byobu new-window -t IEWB:10 -n 'SW4' './IEWB_expect.sh $HOST 10013 $PASS'; 
byobu new-window -t IEWB:11 -n 'BB1' './IEWB_expect.sh $HOST 10007 $PASS'; 
byobu new-window -t IEWB:12 -n 'BB2' './IEWB_expect.sh $HOST 10008 $PASS'; 
byobu new-window -t IEWB:13 -n 'BB3' './IEWB_expect.sh $HOST 10009 $PASS'; 
# Select the window where you want to start
byobu select-window -t IEWB:0; 
# Start byobu with the IEWB session with 256 colors (man tmux)
byobu -2 attach-session -t IEWB

