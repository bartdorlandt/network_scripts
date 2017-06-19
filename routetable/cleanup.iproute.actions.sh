#!/bin/bash

## Variables
SCRIPTDIR=`dirname $0`

echo "What is the router name?"
read ROUTER
export ROUTER=$(echo "${ROUTER,,}")
#echo "Router name is: $ROUTER"

export FULLPATH=`find /regions/*/router/managed -name ${ROUTER}-doc | grep -e "/regions/am" -e "/regions/euaf" -e "/regions/ap"`
if [ -z $FULLPATH ] ; then echo "Router configuration doesn't exits, exiting" ; exit ; fi
echo "Full path to the file is: $FULLPATH"

WORKDIR=$HOME/cleanup/$ROUTER

OSPFonly="20.O"
STATIConly="21.S"
BGPonly="22.B"
MIXSB="23.mixSB"
MIXSO="24.mixSO"
MIXBO="25.mixBO"
MIXBOS="26.mixBOS"

# OUTPUT files
ADDBGPAGGREGATE=30.addBGPaggregate
ADDBGPNETWORK=31.addBGPnetwork
REMOVEBGPNETWORK=32.removeBGPnetwork
REMOVESTATIC=33.removestatic
MANUALCHECK=40.ManualCheck
TMPFILE=TMPFILE
test -f $WORKDIR/$REMOVESTATIC && rm $WORKDIR/$REMOVESTATIC
test -f $WORKDIR/$REMOVEBGPNETWORK && rm $WORKDIR/$REMOVEBGPNETWORK
test -f $WORKDIR/$ADDBGPNETWORK && rm $WORKDIR/$ADDBGPNETWORK
test -f $WORKDIR/$ADDBGPAGGREGATE && rm $WORKDIR/$ADDBGPAGGREGATE
test -f $WORKDIR/$MANUALCHECK && rm $WORKDIR/$MANUALCHECK
test -f $WORKDIR/$TMPFILE && rm $WORKDIR/$TMPFILE


# Saving the IFS
SAVEIFS=$IFS
# Setting the IFS to a new line separator
IFS=$'\n'

### Remove the /32 static routes, gathered in file 01 ###
FILE=11.showiproute-32
cat $WORKDIR/$FILE | grep ^S | awk '{print $2}' | cut -d"/" -f1 | awk '{print "network", $1, "mask 255.255.255.255"}' >> $REMOVEBGPNETWORK
cat $FULLPATH | grep "ip route " | grep 255.255.255.255 >> $WORKDIR/$REMOVESTATIC
### End of /32 static routes ###


### OSPF only ###
#goal: remove static route, leave network statement
for x in `cat $WORKDIR/$OSPFonly | grep "#" | awk '{print $4, $5}'`
do
  cat $FULLPATH | grep $x | grep route >> $WORKDIR/$REMOVESTATIC
done

### Static routes only ###
#goal: remove static route, remove network statement
for x in `cat $WORKDIR/$STATIConly | grep "#" | awk '{print $4, $5}'`
do
  cat $FULLPATH | grep $x | grep route >> $WORKDIR/$REMOVESTATIC
done

for x in `cat $WORKDIR/$STATIConly | grep "#" | awk '{print "network", $4,"mask", $5}'`
do
  cat $FULLPATH | grep $x >> $WORKDIR/$REMOVEBGPNETWORK
done

### BGP routes only ###
#goal: remove static route, remove network statement
for x in `cat $WORKDIR/$BGPonly | grep "#" | awk '{print $4, $5}'`
do
  cat $FULLPATH | grep $x | grep route >> $WORKDIR/$REMOVESTATIC
done

for x in `cat $WORKDIR/$BGPonly | grep "#" | awk '{print "network", $4,"mask", $5}'`
do
  cat $FULLPATH | grep $x >> $WORKDIR/$REMOVEBGPNETWORK
done

### Mix BGP and static routes only ###
#goal: remove static route, remove network statement for the full prefix
for x in `cat $WORKDIR/$MIXSB | grep "#" | awk '{print $4, $5}'`
do
  cat $FULLPATH | grep $x | grep route >> $WORKDIR/$REMOVESTATIC
done

for x in `cat $WORKDIR/$MIXSB | grep "#" | awk '{print "network", $4,"mask", $5}'`
do
  cat $FULLPATH | grep $x >> $WORKDIR/$REMOVEBGPNETWORK
done


### Mix OSPF and static routes only ###
#goal: replace static route with an aggregate-address summary-only
#goal: Add network statements for each OSPF route
#goal: remove static route, remove network statement of the supernet

# replace static supernet routes by aggregate-address summary-only
cat $WORKDIR/$MIXSO | grep "#" | awk '{print "aggregate-address", $4, $5, "summary-only"}' >> $WORKDIR/$ADDBGPAGGREGATE

# add network statements for each OSPF route
cat $WORKDIR/$MIXSO | grep "^O   " | awk '{print $2}' >> $WORKDIR/$TMPFILE
cat $WORKDIR/$MIXSO | grep "^O E1" | awk '{print $3}' >> $WORKDIR/$TMPFILE
cat $WORKDIR/$MIXSO | grep "^O E2" | awk '{print $3}' >> $WORKDIR/$TMPFILE
cat $WORKDIR/$MIXSO | grep "^O IA" | awk '{print $3}' >> $WORKDIR/$TMPFILE
$SCRIPTDIR/slashDecimal2mask_dotted_for_BGP.sh $WORKDIR/$TMPFILE
mv $WORKDIR/$TMPFILE $WORKDIR/$ADDBGPNETWORK

# remove static
for x in `cat $WORKDIR/$MIXSO | grep "#" | awk '{print $4, $5}'`
do
  cat $FULLPATH | grep $x | grep route >> $WORKDIR/$REMOVESTATIC
done
# remove network statement of the supernet
for x in `cat $WORKDIR/$MIXSB | grep "#" | awk '{print "network", $4,"mask", $5}'`
do
  cat $FULLPATH | grep $x >> $WORKDIR/$REMOVEBGPNETWORK
done


### Mix BGP and OSPF ###
#goal: remove static route, leave network statement of the supernet
# Verify this to be sure
for x in `cat $WORKDIR/$MIXBO | grep "#" | awk '{print $4, $5}'`
do
  cat $FULLPATH | grep $x | grep route >> $WORKDIR/$REMOVESTATIC
done

### Mix BGP, OSPF and static ###
# These statements will need to be verified in InfoBlox
# Verify the source file, manual intervention required
echo "The same list as in file $WORKDIR/$MIXBOS" >> $WORKDIR/$MANUALCHECK
echo "These will need to be verified in Infoblox" >> $WORKDIR/$MANUALCHECK
echo "Are these all part of the same site?" >> $WORKDIR/$MANUALCHECK
echo "Should these stay aggregated?" >> $WORKDIR/$MANUALCHECK
echo "should it be replaced by network+Aggregate statements?" >> $WORKDIR/$MANUALCHECK
cat $WORKDIR/$MIXBOS | grep "#"  | awk '{print "show ip route", $4, $5, "long"}' >> $WORKDIR/$MANUALCHECK

# Cleanup and organization
# add BGP aggregate
echo ""
cat $WORKDIR/$ADDBGPAGGREGATE | sort | uniq > $WORKDIR/$ADDBGPAGGREGATE.1
mv $WORKDIR/$ADDBGPAGGREGATE.1 $WORKDIR/$ADDBGPAGGREGATE
echo "File: $WORKDIR/$ADDBGPAGGREGATE"
echo "Aggregate statements to add: `cat $WORKDIR/$ADDBGPAGGREGATE | wc -l`"

# add BGP network
echo ""
cat $WORKDIR/$ADDBGPNETWORK | sort | uniq > $WORKDIR/$ADDBGPNETWORK.1
mv $WORKDIR/$ADDBGPNETWORK.1 $WORKDIR/$ADDBGPNETWORK
echo "File: $WORKDIR/$ADDBGPNETWORK"
echo "network statements to add: `cat $WORKDIR/$ADDBGPNETWORK | wc -l`"

# BGP network removal
echo ""
sed -i 's/network/no network/' $WORKDIR/$REMOVEBGPNETWORK
cat $WORKDIR/$REMOVEBGPNETWORK | sort | uniq > $WORKDIR/$REMOVEBGPNETWORK.1
mv $WORKDIR/$REMOVEBGPNETWORK.1 $WORKDIR/$REMOVEBGPNETWORK
echo "File: $WORKDIR/$REMOVEBGPNETWORK"
echo "network statements to remove: `cat $WORKDIR/$REMOVEBGPNETWORK | wc -l`"

# Static
echo ""
sed -i 's/^ip/no ip/' $WORKDIR/$REMOVESTATIC
cat $WORKDIR/$REMOVESTATIC | sort | uniq > $WORKDIR/$REMOVESTATIC.1
mv $WORKDIR/$REMOVESTATIC.1 $WORKDIR/$REMOVESTATIC
echo "File: $WORKDIR/$REMOVESTATIC"
echo "static routes to remove: `cat $WORKDIR/$REMOVESTATIC | wc -l`"

# Manual check
echo ""
echo "File: $WORKDIR/$MANUALCHECK"
echo "Some subnets to manually verify: `cat $WORKDIR/$MANUALCHECK | wc -l`"


# Restore IFS value
IFS=$SAVEIFS

