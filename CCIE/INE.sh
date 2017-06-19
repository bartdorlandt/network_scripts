#!/bin/sh
echo "What is your password?"
read PASS
export PASS
echo "What is your username?"
read USER
export USER
echo "what is the IP address?"
read HOST
export HOST

# Main account (use the above)
# ./INE_expect.sh $HOST $USER $PASS

# Start a new session with the name INE
byobu new-session -d -s INE; 
# Add a bunch of 'tabs' with corresponding names
byobu new-window -t INE:1 -n 'R1' './INE_expect.sh $HOST ${USER}r1 $PASS'; 
byobu new-window -t INE:2 -n 'R2' './INE_expect.sh $HOST ${USER}r2 $PASS'; 
byobu new-window -t INE:3 -n 'R3' './INE_expect.sh $HOST ${USER}r3 $PASS'; 
byobu new-window -t INE:4 -n 'R4' './INE_expect.sh $HOST ${USER}r4 $PASS'; 
byobu new-window -t INE:5 -n 'R5' './INE_expect.sh $HOST ${USER}r5 $PASS'; 
byobu new-window -t INE:6 -n 'R6' './INE_expect.sh $HOST ${USER}r6 $PASS'; 
byobu new-window -t INE:7 -n 'SW1' './INE_expect.sh $HOST ${USER}sw1 $PASS'; 
byobu new-window -t INE:8 -n 'SW2' './INE_expect.sh $HOST ${USER}sw2 $PASS'; 
byobu new-window -t INE:9 -n 'SW3' './INE_expect.sh $HOST ${USER}sw3 $PASS'; 
byobu new-window -t INE:10 -n 'SW4' './INE_expect.sh $HOST ${USER}sw4 $PASS'; 
byobu new-window -t INE:11 -n 'BB1' './INE_expect.sh $HOST ${USER}bb1 $PASS'; 
byobu new-window -t INE:12 -n 'BB2' './INE_expect.sh $HOST ${USER}bb2 $PASS'; 
byobu new-window -t INE:13 -n 'BB3' './INE_expect.sh $HOST ${USER}bb3 $PASS'; 
byobu new-window -t INE:14 -n 'Main' './INE_expect.sh $HOST ${USER} $PASS'; 
byobu new-window -t INE:15 -n 'Clear' './INE_expect.sh $HOST clear${USER} $PASS'; 
# Select the window where you want to start
#byobu -p R1 -X stuff "uname -a $(echo -ne '\r')"
#byobu -p R1 -X stuff "rsrack10"
byobu select-window -t INE:0; 
# Start byobu with the INE session with 256 colors (man tmux)
byobu -2 attach-session -t INE

