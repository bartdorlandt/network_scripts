#!/bin/bash

if [ ! -d $HOME/tmp ] ; then mkdir $HOME/tmp ; fi

FILE1=$1
FILE2=$2

test -z $FILE1 && echo "additional values expect, script.sh <full_path_file1> <full_path_file2>"
test -z $FILE2 && echo "additional values expect, script.sh <full_path_file1> <full_path_file2>"

TMP1=$HOME/TMP/FILE1
TMP2=$HOME/TMP/FILE2

cat `echo $FILE1` | grep mask | sed -E 's/^[[:space:]]+//' | sort > $TMP1
cat `echo $FILE2` | grep mask | sed -E 's/^[[:space:]]+//' | sort > $TMP2
comm -12 $TMP1 $TMP2
rm $TMP1 $TMP2


