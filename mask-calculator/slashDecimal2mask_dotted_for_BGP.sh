#!/bin/bash

if [ ! -f $1 ]; then
	echo "$1 doesn't exists"
  exit
fi

FILE=$1
sed -i 's@/32@ mask 255.255.255.255@' $FILE
sed -i 's@/31@ mask 255.255.255.254@' $FILE
sed -i 's@/30@ mask 255.255.255.252@' $FILE
sed -i 's@/29@ mask 255.255.255.248@' $FILE
sed -i 's@/28@ mask 255.255.255.240@' $FILE
sed -i 's@/27@ mask 255.255.255.224@' $FILE
sed -i 's@/26@ mask 255.255.255.192@' $FILE
sed -i 's@/25@ mask 255.255.255.128@' $FILE
sed -i 's@/24@ mask 255.255.255.0@' $FILE
sed -i 's@/23@ mask 255.255.254.0@' $FILE
sed -i 's@/22@ mask 255.255.252.0@' $FILE
sed -i 's@/21@ mask 255.255.248.0@' $FILE
sed -i 's@/20@ mask 255.255.240.0@' $FILE
sed -i 's@/19@ mask 255.255.224.0@' $FILE
sed -i 's@/18@ mask 255.255.192.0@' $FILE
sed -i 's@/17@ mask 255.255.128.0@' $FILE
sed -i 's@/16@ mask 255.255.0.0@' $FILE
sed -i 's@/15@ mask 255.254.0.0@' $FILE
sed -i 's@/14@ mask 255.252.0.0@' $FILE
sed -i 's@/13@ mask 255.248.0.0@' $FILE
sed -i 's@/12@ mask 255.240.0.0@' $FILE
sed -i 's@/11@ mask 255.224.0.0@' $FILE
sed -i 's@/10@ mask 255.192.0.0@' $FILE
sed -i 's@/9@ mask 255.128.0.0@' $FILE
sed -i 's@/8@ mask 255.0.0.0@' $FILE
sed -i 's@^@network @' $FILE
