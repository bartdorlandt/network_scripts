#!/bin/bash

INPUTFILE=1.OSPF_input.txt
INPUTCONFILE=1.CONNECTED_input.txt
CURRENTBGP=1.CURRENT_BGP_networks.txt
INPUTFILETMP=tmp.txt
OUTPUTFILE=tmp_BGP_networkstatements.txt
SPECIAL=3.specials.txt
NEWBGPNETWORK=3.newBGPnetwork.txt
REMOVEBGP=3.removeBGPnetwork.txt
CHECKOSPFROUTES=4.checkospfroutes.txt
CHECKNEWROUTES=4.checknewroutes.txt
CHECKSPECIAL=4.checkspecial.txt

if [ ! -f $INPUTFILE ] ; then echo "$INPUTFILE file is missing, exiting" ;  exit ; fi
if [ ! -f $INPUTCONFILE ] ; then echo "$INPUTCONFILE file is missing, exiting" ; exit ; fi
if [ ! -f $CURRENTBGP ] ; then  echo "$CURRENTBGP file is missing, exiting" ; exit ; fi

for x in $SPECIAL $CHECKSPECIAL $OUTPUTFILE $CHECKNEWROUTES $CHECKOSPFROUTES $NEWBGPNETWORK $REMOVEBGP ; do if [ -f $x ] ; then rm $x ; fi ; done

#echo "Organize input"
sed -i '/^$/d' $INPUTFILE
cat $INPUTFILE | grep -v 9999 | grep -e "tag 0" -e Intra | awk '{print $2}' | cut -d"," -f1 | grep -v "0.0.0.0/0" >> $INPUTFILETMP
sed -i '/^$/d' $INPUTCONFILE
cat $INPUTCONFILE | grep "/" | awk '{print $2}' >> $INPUTFILETMP

#echo "rewrite to BGP network statements"
sed -i 's@/32@ mask 255.255.255.255@' $INPUTFILETMP
sed -i 's@/31@ mask 255.255.255.254@' $INPUTFILETMP
sed -i 's@/30@ mask 255.255.255.252@' $INPUTFILETMP
sed -i 's@/29@ mask 255.255.255.248@' $INPUTFILETMP
sed -i 's@/28@ mask 255.255.255.240@' $INPUTFILETMP
sed -i 's@/27@ mask 255.255.255.224@' $INPUTFILETMP
sed -i 's@/26@ mask 255.255.255.192@' $INPUTFILETMP
sed -i 's@/25@ mask 255.255.255.128@' $INPUTFILETMP
sed -i 's@/24@ mask 255.255.255.0@' $INPUTFILETMP
sed -i 's@/23@ mask 255.255.254.0@' $INPUTFILETMP
sed -i 's@/22@ mask 255.255.252.0@' $INPUTFILETMP
sed -i 's@/21@ mask 255.255.248.0@' $INPUTFILETMP
sed -i 's@/20@ mask 255.255.240.0@' $INPUTFILETMP
sed -i 's@/19@ mask 255.255.224.0@' $INPUTFILETMP
sed -i 's@/18@ mask 255.255.192.0@' $INPUTFILETMP
sed -i 's@/17@ mask 255.255.128.0@' $INPUTFILETMP
sed -i 's@/16@ mask 255.255.0.0@' $INPUTFILETMP
sed -i 's@/15@ mask 255.254.0.0@' $INPUTFILETMP
sed -i 's@/14@ mask 255.252.0.0@' $INPUTFILETMP
sed -i 's@/13@ mask 255.248.0.0@' $INPUTFILETMP
sed -i 's@/12@ mask 255.240.0.0@' $INPUTFILETMP
sed -i 's@/11@ mask 255.224.0.0@' $INPUTFILETMP
sed -i 's@/10@ mask 255.192.0.0@' $INPUTFILETMP
sed -i 's@/9@ mask 255.128.0.0@' $INPUTFILETMP
sed -i 's@/8@ mask 255.0.0.0@' $INPUTFILETMP
sed -i 's@^@network @' $INPUTFILETMP

cat $INPUTFILETMP | sort | uniq > $OUTPUTFILE

#echo "sorting & organizing Current BGP networks"
sed -i '/^$/d' $CURRENTBGP
sed -i '/area/d' $CURRENTBGP
sed -i 's@^[ \s]*network@network@' $CURRENTBGP
echo "! These are BGP network statements that have no mask. Please work on these manually" > $SPECIAL
echo "! Please look at the file: $CHECKSPECIAL to make your life easier" >> $SPECIAL
grep -v mask $CURRENTBGP >> $SPECIAL

# Needed for the for loop, to match a full line instead of a per word basis
SAVEIFS=$IFS
IFS=$'\n'
################
#echo "Existing in OSPF, but not known in BGP as a network statement"
################
# Verify if the current BGP table, already has these statements, if so, not printed
echo "! This file show all the BGP networks that can be added." >> $NEWBGPNETWORK
echo "! Please make sure this is meant to be added." >> $NEWBGPNETWORK
echo "! Verify the source of the OSPF route. Verify if you want to add it into BGP" >> $NEWBGPNETWORK
echo "! Use the following script to test the routes: $CHECKNEWROUTES" >>  $NEWBGPNETWORK
for x in `cat $OUTPUTFILE` 
do if [ ! "$x" = "`cat $CURRENTBGP | grep $x`" ] ; then 
    echo $x >> $NEWBGPNETWORK
#  else 
#  echo $x exists 
fi  
done
# Rewritten the code to do sh ip route command to easily verify its source.
echo "! Use the following output to easily paste it into the router" > $CHECKNEWROUTES
cat $NEWBGPNETWORK | grep -v "^\!" | cut -d" " -f1,2,4 | sed 's@network @sh ip route @' >> $CHECKNEWROUTES



################
# These network statements can be removed, please verify to be certain
################
echo "! This file show all the BGP networks that can be removed." >> $REMOVEBGP
echo "! A test script can be found in file: $CHECKOSPFROUTES" >> $REMOVEBGP
for x in `cat $CURRENTBGP | grep mask`
do if [ ! "$x" = "`cat $OUTPUTFILE | grep $x`" ] ; then
    echo $x >> $REMOVEBGP
#  else
#  echo $x exists
fi
done
echo "! Use the following output to easily paste it into the router" > $CHECKOSPFROUTES
cat $REMOVEBGP | grep -v "^\!" | cut -d" " -f1,2,4 | sed 's@network @sh ip route @' >> $CHECKOSPFROUTES
# change the network to 'no network'.
sed -i 's@^network@no network@' $REMOVEBGP

echo "! Use the following output to easily paste it into the router" > $CHECKSPECIAL
echo "! Do mind to look for an exact match, most probably a /16" >> $CHECKSPECIAL
cat $SPECIAL | grep -v "^\!" | sed 's@network @sh ip route @' >> $CHECKSPECIAL


# Restore IFS value
IFS=$SAVEIFS

# remove unnecessary files
for x in $INPUTFILETMP $OUTPUTFILE ; do if [ -f $x ] ; then rm $x ; fi ; done

echo "See files starting with 3 and 4"
