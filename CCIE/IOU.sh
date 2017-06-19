#!/bin/sh
export HOST=192.168.2.219

# if one session is lost, open a new virt. window (F2) and do 
# telnet 46.28.145.112 <port>
# log in with the password, after this you could rename the window with F8.

# Start a new session with the name IOU
byobu new-session -d -s IOU; 
# Add a bunch of 'tabs' with corresponding names
byobu new-window -t IOU:1 -n 'R1' './IOU_expect.sh $HOST 2001 $PASS'; 
byobu new-window -t IOU:2 -n 'R2' './IOU_expect.sh $HOST 2002 $PASS'; 
byobu new-window -t IOU:3 -n 'R3' './IOU_expect.sh $HOST 2003 $PASS'; 
byobu new-window -t IOU:4 -n 'R4' './IOU_expect.sh $HOST 2004 $PASS'; 
byobu new-window -t IOU:5 -n 'R5' './IOU_expect.sh $HOST 2005 $PASS'; 
byobu new-window -t IOU:6 -n 'SW1' './IOU_expect.sh $HOST 2006 $PASS'; 
byobu new-window -t IOU:7 -n 'SW2' './IOU_expect.sh $HOST 2007 $PASS'; 
byobu new-window -t IOU:8 -n 'SW3' './IOU_expect.sh $HOST 2008 $PASS'; 
byobu new-window -t IOU:9 -n 'SW4' './IOU_expect.sh $HOST 2009 $PASS'; 
byobu new-window -t IOU:10 -n 'BB1' './IOU_expect.sh $HOST 2010 $PASS'; 
byobu new-window -t IOU:11 -n 'BB2' './IOU_expect.sh $HOST 2011 $PASS'; 
byobu new-window -t IOU:12 -n 'BB3' './IOU_expect.sh $HOST 2012 $PASS'; 
# Select the window where you want to start
byobu select-window -t IOU:0; 
# Start byobu with the IOU session with 256 colors (man tmux)
byobu -2 attach-session -t IOU

