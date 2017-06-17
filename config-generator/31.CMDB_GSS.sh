#!/bin/bash

# This file should provide most of the information, required for the Assyst CMDB info.
export CMDBOUTPUT=$OUTPUTDIR/CMDB.txt
export GSSOUTPUT=$OUTPUTDIR/GSS_add_maintenance.txt

KEYAPPEND=""


################ CMDB output #####################
if [ ! -f $CMDBOUTPUT ] ; then
cat > $CMDBOUTPUT << EOF
# Assyst information
# URL: http://srpweb301070:7777/assystweb/application.do
# Menu > Configuration > Product Structure > Item
#
Location: $VARSITEID

# User box
User:       
Section:    CORPORATE ICT
Building:   $VARSITEID

# Select the following buttons, regarding logging and Cause.
Incident Logging, Problem Logging, Change Logging
Incident Cause,   Problem Cause,   Change Cause


# Following switch dependent information:
EOF
fi

i="1"

while [ $i -lt $STACKAMOUNT ] ; do
	WHILETAG=$(eval echo $`echo TAG$i`)
	WHILEHARDWARE=$(eval echo $`echo HARDWARE$i`)
  if [ "`echo $WHILEHARDWARE | grep 24`" = "`echo $WHILEHARDWARE`" ] ; then
    ASSYSTPRODUCT="EDGE SW24 IPO"
  fi
  if [ "`echo $WHILEHARDWARE | grep 48`" = "`echo $WHILEHARDWARE`" ] ; then
    ASSYSTPRODUCT="EDGE SW48 IPO"
  fi
  if [ $i -gt 1 ] ; then
    KEYAPPEND="_$i"
  fi
# Info for Assyst CMDB
  if [ -z "`cat $CMDBOUTPUT | grep $WHILETAG`" ] ; then
cat >> $CMDBOUTPUT << EOF
# Mainbox - Switch $i
Shortcode:                $WHILETAG
Name:                     ${VARHOSTNAME}$KEYAPPEND
Customer Service Group:   ICT
Serial:                   $(eval echo $`echo SERIALNUMBER$i`)
Key A:                    ${VARSWITCHIPADDRESS}$KEYAPPEND
Status:                   MANAGED
Icon:                     CRITICAL ITEM
Acquired:                 `date +%Y-%m-%d`

# Product box
Product Class:      LAN/WAN COMPON.
Product:            $ASSYSTPRODUCT
Supplier:           Cisco
Supplier Ref:       $WHILEHARDWARE

EOF
fi
  i=$[$i+1]
done

################ GSS output #####################
if [ ! -f $GSSOUTPUT ] ; then
cat > $GSSOUTPUT << EOF
# Add the following lines to the 'add and remove from FrieslandCampina' excel file
# Source: http://our.frieslandcampina.biz/disciplines/100006/100124/connectivity/services/GSS/Forms/AllItems.aspx
# Location information can be found here:
# http://our.frieslandcampina.biz/disciplines/100010/com/Locations%20worldwide/Forms/AllItems.aspx
EOF
fi


i="1"
#
while [ $i -lt $STACKAMOUNT ] ; do
	WHILETAG=$(eval echo $`echo TAG$i`)
	WHILEHARDWARE=$(eval echo $`echo HARDWARE$i`)

	if [ -z "`cat $GSSOUTPUT | grep $WHILETAG`" ] ; then
		#date, add, asset, serial, part#, Sitecode, location, City, Contact, Phone, Email
		echo "`date +%Y-%m-%d`, add, $WHILETAG, $(eval echo $`echo SERIALNUMBER$i`), $WHILEHARDWARE ,$VARSITEID, address, $VARCITYNAME, contact, Phone, Email" >> $GSSOUTPUT
	fi
	i=$[$i+1]
done

