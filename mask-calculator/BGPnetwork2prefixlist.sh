#!/bin/bash

if [ -z $1 ] || [ -z $2 ] ; then
  echo "additional values expect, script INPUTFILE PREFIXLIST_name"
  echo "input file looks like: network 1.2.3.4 mask 255.255.255.255"
  exit
fi

# INPUT File has a BGP network syntax
# network 1.2.3.4 mask 255.255.255.255

FILE=$1
PREFIXLIST=$2

# output should look like "ip prefix-list static-ospf-filter seq 30 permit 196.8.88.52/32"
#echo $1
#echo $2

sed -i 's@ mask 255.255.255.255@/32@' $FILE
sed -i 's@ mask 255.255.255.254@/31@' $FILE
sed -i 's@ mask 255.255.255.252@/30@' $FILE
sed -i 's@ mask 255.255.255.248@/29@' $FILE
sed -i 's@ mask 255.255.255.240@/28@' $FILE
sed -i 's@ mask 255.255.255.224@/27@' $FILE
sed -i 's@ mask 255.255.255.192@/26@' $FILE
sed -i 's@ mask 255.255.255.128@/25@' $FILE
sed -i 's@ mask 255.255.255.0@/24@' $FILE
sed -i 's@ mask 255.255.254.0@/23@' $FILE
sed -i 's@ mask 255.255.252.0@/22@' $FILE
sed -i 's@ mask 255.255.248.0@/21@' $FILE
sed -i 's@ mask 255.255.240.0@/20@' $FILE
sed -i 's@ mask 255.255.224.0@/19@' $FILE
sed -i 's@ mask 255.255.192.0@/18@' $FILE
sed -i 's@ mask 255.255.128.0@/17@' $FILE
sed -i 's@ mask 255.255.0.0@/16@' $FILE
sed -i 's@ mask 255.254.0.0@/15@' $FILE
sed -i 's@ mask 255.252.0.0@/14@' $FILE
sed -i 's@ mask 255.248.0.0@/13@' $FILE
sed -i 's@ mask 255.240.0.0@/12@' $FILE
sed -i 's@ mask 255.224.0.0@/11@' $FILE
sed -i 's@ mask 255.192.0.0@/10@' $FILE
sed -i 's@ mask 255.128.0.0@/9@' $FILE
sed -i 's@ mask 255.0.0.0@/8@' $FILE
sed -i 's@network @ip prefix-list '$PREFIXLIST' permit @' $FILE

