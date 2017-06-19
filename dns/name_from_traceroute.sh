#!/bin/bash

INPUT=input
for x in `cat $INPUT | awk '{print $2}' | grep -v "*"`
do
  NAME=`nslookup $x | grep name | awk '{print $4}'`
  if [ -z $NAME ] ; then
    echo -e "$x \t = No hostname in DNS"
  else
    echo -e "$x \t = $NAME"
  fi
done
