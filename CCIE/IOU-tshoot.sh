#!/bin/sh
export HOST=192.168.2.219

# Start a new session with the name IOU
byobu new-session -d -s IOU; 
# Add a bunch of 'tabs' with corresponding names
byobu new-window -t IOU:1 -n 'R1' './IOU_expect.sh $HOST 2001 $PASS'; 
byobu new-window -t IOU:2 -n 'R2' './IOU_expect.sh $HOST 2002 $PASS'; 
byobu new-window -t IOU:3 -n 'R3' './IOU_expect.sh $HOST 2003 $PASS'; 
byobu new-window -t IOU:4 -n 'R4' './IOU_expect.sh $HOST 2004 $PASS'; 
byobu new-window -t IOU:5 -n 'R5' './IOU_expect.sh $HOST 2005 $PASS'; 
byobu new-window -t IOU:6 -n 'R6' './IOU_expect.sh $HOST 2006 $PASS'; 
byobu new-window -t IOU:7 -n 'R7' './IOU_expect.sh $HOST 2007 $PASS'; 
byobu new-window -t IOU:8 -n 'R8' './IOU_expect.sh $HOST 2008 $PASS'; 
byobu new-window -t IOU:9 -n 'R9' './IOU_expect.sh $HOST 2009 $PASS'; 
byobu new-window -t IOU:10 -n 'R10' './IOU_expect.sh $HOST 2010 $PASS'; 
byobu new-window -t IOU:11 -n 'R11' './IOU_expect.sh $HOST 2011 $PASS'; 
byobu new-window -t IOU:12 -n 'R12' './IOU_expect.sh $HOST 2012 $PASS'; 
byobu new-window -t IOU:13 -n 'R13' './IOU_expect.sh $HOST 2013 $PASS'; 
byobu new-window -t IOU:14 -n 'R14' './IOU_expect.sh $HOST 2014 $PASS'; 
byobu new-window -t IOU:15 -n 'R15' './IOU_expect.sh $HOST 2015 $PASS'; 
byobu new-window -t IOU:16 -n 'R16' './IOU_expect.sh $HOST 2016 $PASS'; 
byobu new-window -t IOU:17 -n 'R17' './IOU_expect.sh $HOST 2017 $PASS'; 
byobu new-window -t IOU:18 -n 'R18' './IOU_expect.sh $HOST 2018 $PASS'; 
byobu new-window -t IOU:19 -n 'R19' './IOU_expect.sh $HOST 2019 $PASS'; 
byobu new-window -t IOU:20 -n 'R20' './IOU_expect.sh $HOST 2020 $PASS'; 
byobu new-window -t IOU:21 -n 'R21' './IOU_expect.sh $HOST 2021 $PASS'; 
byobu new-window -t IOU:22 -n 'R22' './IOU_expect.sh $HOST 2022 $PASS'; 
byobu new-window -t IOU:23 -n 'R23' './IOU_expect.sh $HOST 2023 $PASS'; 
byobu new-window -t IOU:24 -n 'R24' './IOU_expect.sh $HOST 2024 $PASS'; 
byobu new-window -t IOU:25 -n 'R25' './IOU_expect.sh $HOST 2025 $PASS'; 
byobu new-window -t IOU:26 -n 'R26' './IOU_expect.sh $HOST 2026 $PASS'; 
byobu new-window -t IOU:27 -n 'R27' './IOU_expect.sh $HOST 2027 $PASS'; 
byobu new-window -t IOU:28 -n 'R28' './IOU_expect.sh $HOST 2028 $PASS'; 
byobu new-window -t IOU:29 -n 'R29' './IOU_expect.sh $HOST 2029 $PASS'; 
byobu new-window -t IOU:30 -n 'R30' './IOU_expect.sh $HOST 2030 $PASS'; 
byobu new-window -t IOU:31 -n 'R31' './IOU_expect.sh $HOST 2031 $PASS'; 
byobu new-window -t IOU:32 -n 'R32' './IOU_expect.sh $HOST 2032 $PASS'; 
byobu new-window -t IOU:33 -n 'R33' './IOU_expect.sh $HOST 2033 $PASS'; 
byobu new-window -t IOU:34 -n 'R34' './IOU_expect.sh $HOST 2034 $PASS'; 
byobu new-window -t IOU:35 -n 'R35' './IOU_expect.sh $HOST 2035 $PASS'; 
byobu new-window -t IOU:36 -n 'R36' './IOU_expect.sh $HOST 2036 $PASS'; 
byobu new-window -t IOU:42 -n 'R42' './IOU_expect.sh $HOST 2042 $PASS'; 
byobu new-window -t IOU:51 -n 'R51' './IOU_expect.sh $HOST 2051 $PASS'; 
byobu new-window -t IOU:52 -n 'R52' './IOU_expect.sh $HOST 2052 $PASS'; 
byobu new-window -t IOU:53 -n 'R53' './IOU_expect.sh $HOST 2053 $PASS'; 
byobu new-window -t IOU:54 -n 'R54' './IOU_expect.sh $HOST 2054 $PASS'; 
byobu new-window -t IOU:55 -n 'R55' './IOU_expect.sh $HOST 2055 $PASS'; 
byobu new-window -t IOU:56 -n 'R56' './IOU_expect.sh $HOST 2056 $PASS'; 
byobu new-window -t IOU:61 -n 'R61' './IOU_expect.sh $HOST 2061 $PASS'; 
# Select the window where you want to start
byobu select-window -t IOU:0; 
# Start byobu with the IOU session with 256 colors (man tmux)
byobu -2 attach-session -t IOU

