#!/bin/sh

## Variables
SCRIPTDIR=`dirname $0`

echo "What is the router name?"
read ROUTER
export ROUTER=$(echo "${ROUTER,,}")
#echo "Router name is: $ROUTER"

export FULLPATH=`find /regions/*/router/managed -name ${ROUTER}-doc | grep -e "/regions/am" -e "/regions/euaf" -e "/regions/ap"`
if [ -z $FULLPATH ] ; then echo "Router configuration doesn't exits, exiting" ; exit ; fi
echo "Full path to the file is: $FULLPATH"

# Create the cleanup dir if it doesn't exists
export WORKDIR="$HOME/cleanup/${ROUTER}_network"
echo "cleanup dir: $WORKDIR"
if [ -d $WORKDIR ] ; then
  echo "cleanup directory already exists, do you want to delete it?"
  echo "yes/no"
  read DELETE
  if [ "$DELETE" == "yes" ] ; then
    rm -rf $WORKDIR
  else
    echo "you chose not to delete it, manual action required. The script will end"
    exit
  fi
fi
test ! -d $WORKDIR && mkdir -p $WORKDIR
echo ""

echo "Provide the password for the do_tool"
read -s PASSWORD

# OUTPUT files
REMOVEBGPNETWORK=30.removeBGPnetwork
REMOVEBGPNETWORKSPECIAL=31.removeBGPnetwork_special
SORTSTATIC=32.sortstatic
test -f $WORKDIR/$SORTSTATIC && rm -f $WORKDIR/$SORTSTATIC
test -f $WORKDIR/$REMOVEBGPNETWORK && rm -f $WORKDIR/$REMOVEBGPNETWORK
test -f $WORKDIR/$REMOVEBGPNETWORKSPECIAL && rm -f $WORKDIR/$REMOVEBGPNETWORKSPECIAL

FILE=01.config_mask_to_routes
echo "Extract and convert BGP network to show ip routes, file: $WORKDIR/$FILE"
# adding the "ter le 0" command upfront
echo "ter le 0" > $WORKDIR/$FILE
cat $FULLPATH | grep " mask " | awk '{print "sh ip ro", $2, $4, "| i Known|table"}' >> $WORKDIR/$FILE

# Exectuing the contents of 03.showiproutes-non32 on the router
OUTPUT=10.showiproutes
echo "Executing the contents of $WORKDIR/$FILE on router: $ROUTER"
# script.pl <router> <outputfile> <inputfile>
$SCRIPTDIR/telnet.pl $ROUTER $WORKDIR/$OUTPUT $WORKDIR/$FILE do_tool $PASSWORD > /dev/null 2&>1
sed -i '/ter le 0/d'  $WORKDIR/$OUTPUT
export ROUTERUP=$(echo "${ROUTER^^}")
sed -i "/^${ROUTERUP}#$/d"  $WORKDIR/$OUTPUT

# Separate the info
cat $WORKDIR/$OUTPUT | grep -B1 ospf | grep -v "\-\-" > $WORKDIR/20.O
cat $WORKDIR/$OUTPUT | grep -B1 static | grep -v "\-\-" > $WORKDIR/21.S
cat $WORKDIR/$OUTPUT | grep -B1 connected | grep -v "\-\-" > $WORKDIR/22.C
cat $WORKDIR/$OUTPUT | grep -B1 "not in table" | grep -v "\-\-" > $WORKDIR/23.N
cat $WORKDIR/$OUTPUT | grep -B1 "bgp" | grep -v "\-\-" > $WORKDIR/24.B

# Saving the IFS
SAVEIFS=$IFS
# Setting the IFS to a new line separator
IFS=$'\n'

for x in `cat $WORKDIR/23.N | grep "#" | awk '{print "network", $4,"mask", $5}'`
do
  cat $FULLPATH | grep $x | grep -v route-map >> $WORKDIR/$REMOVEBGPNETWORK
  cat $FULLPATH | grep $x | grep route-map >> $WORKDIR/$REMOVEBGPNETWORKSPECIAL
done
for x in `cat $WORKDIR/24.B | grep "#" | awk '{print "network", $4,"mask", $5}'`
do
  cat $FULLPATH | grep $x | grep -v route-map >> $WORKDIR/$REMOVEBGPNETWORK
  cat $FULLPATH | grep $x | grep route-map >> $WORKDIR/$REMOVEBGPNETWORKSPECIAL
done

# Preparing some statics for manual investigation
for x in `cat $WORKDIR/21.S | grep "#" | awk '{print "sh ip ro", $4, $5, "l"}'`
do
  echo $x >> $WORKDIR/$SORTSTATIC
done

# BGP network removal
echo ""
sed -i 's/network/no network/' $WORKDIR/$REMOVEBGPNETWORK
cat $WORKDIR/$REMOVEBGPNETWORK | sort | uniq > $WORKDIR/$REMOVEBGPNETWORK.1
mv $WORKDIR/$REMOVEBGPNETWORK.1 $WORKDIR/$REMOVEBGPNETWORK
echo ""
echo "*** Output ***"
echo ""
echo "File: $WORKDIR/$REMOVEBGPNETWORK"
echo "network statements to remove: `cat $WORKDIR/$REMOVEBGPNETWORK | wc -l`"

# BGP special removal
echo ""
echo ""
sed -i 's/network/no network/' $WORKDIR/$REMOVEBGPNETWORKSPECIAL
#cat $WORKDIR/$REMOVEBGPNETWORKSPECIAL | sort | uniq > $WORKDIR/$REMOVEBGPNETWORKSPECIAL.1
#mv $WORKDIR/$REMOVEBGPNETWORKSPECIAL.1 $WORKDIR/$REMOVEBGPNETWORKSPECIAL
echo "There is a special file which include BGP network statements with a route-map configured. These are listed in a separate file:"
echo "File: $WORKDIR/$REMOVEBGPNETWORKSPECIAL"
#echo "network statements to remove: `cat $WORKDIR/$REMOVEBGPNETWORKSPECIAL | wc -l`"
echo "Including `wc -l $WORKDIR/$REMOVEBGPNETWORKSPECIAL` lines"

echo ""
echo ""
echo "The contents of files $WORKDIR/20.O, 22.C are fine"
echo ""
echo "The contents of file $WORKDIR/23.N have been converted to $WORKDIR/$REMOVEBGPNETWORK and should be removed"
echo ""
echo "The static route matches need further investigation"
echo "use the other script to figure out what to do with them"
echo "a total of `cat $WORKDIR/21.S | grep \# | wc -l` need to be sorted"
echo "the show ip route longer commands can be found in: $WORKDIR/$SORTSTATIC"
echo ""
echo ""

# Restore IFS value
IFS=$SAVEIFS

