#!/bin/sh

## Variables
SCRIPTDIR=`dirname $0`

echo "What is the router name?"
read ROUTER
#ROUTER=$(echo "$ROUTER" | tr '[:upper:]' '[:lower:]')
export ROUTER=$(echo "${ROUTER,,}")
echo "Router name is: $ROUTER"

export FULLPATH=`find /regions/*/router/managed -name ${ROUTER}-doc | grep -e "/regions/am" -e "/regions/euaf" -e "/regions/ap"`
if [ -z $FULLPATH ] ; then echo "Router configuration doesn't exits, exiting" ; exit ; fi
echo "Full path to the file is: $FULLPATH"

# Create the cleanup dir if it doesn't exists
export WORKDIR="$HOME/cleanup/$ROUTER"
if [ -d $WORKDIR ] ; then
  echo "cleanup directory already exists, do you want to delete it?"
  echo "NOTE: your manually splitted files will be deleted as well"
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
echo ""

#### First do the /32 static routes ###
### Find all /32 routes that only exists via statics.
FILE=06.static-routes-32
cat $FULLPATH | grep "ip route" | awk '{print "sh ip ro", $3 , $4, "l | i ^S"}' | sort | uniq  | grep 255.255.255.255 > $WORKDIR/$FILE

# Exectuing the contents of 03.showiproutes-non32 on the router
OUTPUT=11.showiproute-32
echo "Executing the content of $WORKDIR/$FILE on router: $ROUTER"
# script.pl <router> <outputfile> <inputfile>
$SCRIPTDIR/telnet.pl $ROUTER $WORKDIR/$OUTPUT $WORKDIR/$FILE do_tool $PASSWORD >/dev/null 2>&1
echo ""
#sed -i '/ter le 0/d'  $WORKDIR/$OUTPUT
export ROUTERUP=$(echo "${ROUTER^^}")
sed -i "/^${ROUTERUP}#$/d" $WORKDIR/$OUTPUT

#### End of /32 Static routes ###


# Extract all BGP network statements
FILE=01.bgp-network-non32
echo "Extract all BGP network statements, except /32 to: $WORKDIR/$FILE"
cat $FULLPATH | grep mask | grep -v 255.255.255.255 | sed -E 's/^[[:space:]]+//' > $WORKDIR/$FILE

# Extract all static routes
FILE=02.static-routes-non32
echo "Extract static routes to show ip routes, file: $WORKDIR/$FILE"
cat $FULLPATH | grep "ip route" | grep -v 255.255.255.255 > $WORKDIR/$FILE

# Extract and convert static routes to show ip routes
FILE=03.showiproutes-non32
echo "Extract and convert static routes to show ip routes, file: $WORKDIR/$FILE"
# adding the "ter le 0" command upfront
echo "ter le 0" > $WORKDIR/$FILE
cat $FULLPATH | grep "ip route " | grep -v "127.0.0.0 255.0.0.0" |  grep -v 255.255.255.255 | sed 's/^ip route/sh ip ro/' | awk '{print $1, $2, $3, $4, $5, "l | i ^S|^B|^O" }' | sort | uniq >> $WORKDIR/$FILE

# Exectuing the contents of 03.showiproutes-non32 on the router
OUTPUT=10.showiproute-non32
echo "Executing the content of $WORKDIR/$FILE on router: $ROUTER"
# script.pl <router> <outputfile> <inputfile>
$SCRIPTDIR/telnet.pl $ROUTER $WORKDIR/$OUTPUT $WORKDIR/$FILE do_tool $PASSWORD >/dev/null 2>&1
echo ""
sed -i '/ter le 0/d'  $WORKDIR/$OUTPUT
export ROUTERUP=$(echo "${ROUTER^^}")
sed -i "/^${ROUTERUP}#$/d"  $WORKDIR/$OUTPUT

# Copy the output file to multiple files to be splitted (manually).
echo "Copying the output of the router to multiple files for manual processing"
for x in 20.O 21.S 22.B 23.mixSB 24.mixSO 25.mixBO 26.mixBOS ; do cp -a $WORKDIR/$OUTPUT $WORKDIR/$x ; done
echo ""
echo "What to do:"
echo "Edit all the files and exclude all entries that don't belong to the file."
echo "e.g. The following belongs only to the O-file (20.O)"
echo ""
echo "NLAMSDC1MP888#show ip route 10.126.240.0 255.255.255.0 longer | i ^S|^B|^O"
echo "O E2     10.126.240.0/24"
echo "It has an exact match and no more specific entries."
echo ""
echo ""
echo "Only to the S file (21.S)"
echo "NLAMSDC1MP888#show ip route 10.126.80.0 255.255.255.0 longer | i ^S|^B|^O"
echo "S        10.126.80.0/24 [250/0] via 32.37.209.8"
echo ""
echo ""
echo "Only to the mixSO (24.mixSO)"
echo "NLAMSDC1MP888#show ip route 10.127.193.224 255.255.255.224 longer | i ^S|^B|^O"
echo "S        10.127.193.224/27 [250/0] via 32.37.209.8"
echo "O E1     10.127.193.224/28"
echo "O E1     10.127.193.240/28"
echo ""
echo ""

