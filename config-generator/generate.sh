#!/bin/bash
# Version 0.2
#   changed the port layout. 
#   Fixed the output if it is only 1 switch, thus not a stack.
#   CMDB and GSS output improved with more information.
#
SCRIPTDIR=`dirname $0`
VARDIR=`dirname $1`
export DATE=`date +%Y%m%d_%H%M`

# Load the added Variables file or the default one
VARFILE=$1
if [ ! "$VARFILE" = "" ] ; then
	#echo VARDIR = $VARDIR
	#echo VARFILE = $VARFILE
	if [ "$VARDIR" = "." ] ; then echo "Use the full path for the variables. Exiting" ; exit ; fi
	if [ ! -f $VARFILE ] ; then echo "File doesn't exists, exting" ; exit ; fi
	echo "Using the different Variables file: "
    echo -e "\t$VARFILE"
	#VARFILE=$VARFILE
else
	# First, load all variables
	VARFILE=01.variables.txt
	echo "Using the default Variables file: "
  echo -e "\t$SCRIPTDIR/$VARFILE"
fi
#echo $VARFILE
. $VARFILE
# Other variables
GLOBALTEMPLATE=$SCRIPTDIR/10.global_template.sh
ACCESSSWITCHTEMPLATE=$SCRIPTDIR/11.accessswitch_template.sh
TACACSTEMPLATE=$SCRIPTDIR/12.tacacs_template.sh
TACACSOLDTEMPLATE=$SCRIPTDIR/13.tacacsOLD_template.sh
STACKBANNERTEMPLATE=$SCRIPTDIR/15.stackbanner_part2_template.sh
ENDGLOBALTEMPLATE=$SCRIPTDIR/19.endglobal_template.sh
L3SWITCHTEMPLATE=$SCRIPTDIR/20.L3switch_template.sh
L3VLANTEMPLATE=$SCRIPTDIR/21.L3switch_VLAN_template.sh
PORTSTEMPLATE=$SCRIPTDIR/30.ports_template.sh
CMDBGSSTEMPLATE=$SCRIPTDIR/31.CMDB_GSS.sh

# Created output directory, based on siteID
export OUTPUTDIR=$HOME/generatedconfigs/$VARSITEID
test ! -d $OUTPUTDIR && mkdir -p $OUTPUTDIR
export OUTPUTFILE=$OUTPUTDIR/$VARHOSTNAME

if [ -f $OUTPUTFILE ] ; then 
	echo "Output file already exitst. Moved it to: "
  echo -e "\t${OUTPUTFILE}_$DATE"
	mv $OUTPUTFILE ${OUTPUTFILE}_$DATE
fi


mod_global () {
  echo ""
  echo "Starting the different sections:"
	echo -e "\t10, global template"
	. $GLOBALTEMPLATE
	# is this a non-K9 IOS. Remove SSH related stuf.
	if [ "$K9" = "no" ] ; then
		sed -i 's/transport input ssh/transport input telnet/' $OUTPUTFILE
		sed '/crypto key generate rsa usage-keys modulus 2048/d' $OUTPUTFILE
	fi
	# TACACS
	echo -e "\t12, tacacs"
	. $TACACSTEMPLATE
	# 6500 ?
	if [ "$SWITCH6500" = "yes" ] ; then
		echo -e "\t6500 config"
  	echo "! 6500 config part" >> $OUTPUTFILE
  	echo "Transceiver type all" >> $OUTPUTFILE
  	echo " monitoring" >> $OUTPUTFILE
	fi
	if [ "$(echo $VARSITEID | cut -c1-2)" = "DE" ] ; then
		echo -e "\tGerman dependency"
		echo "! German configuration part" >> $OUTPUTFILE
		echo "username netad21 privilege 15 secret 0 21Quark*" >> $OUTPUTFILE
	fi
}
mod_access () {
	echo -e "\t11, Access switch template"
	. $ACCESSSWITCHTEMPLATE
}
mod_stack () {
	# Check if it is a stack. Generate stack related config
	if [ "$STACK" = "no" ] ; then 
		echo -e "\t\tsingle stack"
		export STACKAMOUNT="2"
	else
		echo -e "\t\tmulti stack"
		echo -e "\t\tStack Amount = $STACKAMOUNT"
		export STACKAMOUNT=$[$STACKAMOUNT+1]
	fi
	echo -e "\t15, banner"
	. $STACKBANNERTEMPLATE
}
mod_L3 () {
	# L3 script
	echo -e "\t20, L3"
	. $L3SWITCHTEMPLATE
	. $L3VLANTEMPLATE
}
#mod_VSS () {
#	# VSS script
#}
mod_finish () {
	echo -e "\tlast part global template"
	. $ENDGLOBALTEMPLATE
  echo ""
	echo "Finishing configuration"
	echo "!!!!!!!!!!!!!!!!!!!!!" >> $OUTPUTFILE
	echo "!!!  Do not forget:" >> $OUTPUTFILE
	echo "!!!  -  Shutdown unused ports" >> $OUTPUTFILE
	echo "!!!  -  Put a description on the uplink ports" >> $OUTPUTFILE
	echo "!!!  -  See the generated ports file for examples" >> $OUTPUTFILE
	echo "!!!" >> $OUTPUTFILE
	#echo "" >> $OUTPUTFILE
	#echo "" >> $OUTPUTFILE
	#echo "" >> $OUTPUTFILE
	echo "end" >> $OUTPUTFILE
	echo -e "\tThis configuration doesn't have any ports yet, except for management"
	echo -e "\toutput file: "
  echo -e "\t\t$OUTPUTFILE"
}

mod_ports () {
  echo ""
	echo "Do you want to create a port template file? This will be created in a separate file"
	echo " yes / no ?"
	read DOPORTS
	if [ "$DOPORTS" = "yes" ] ; then 
    echo ""
		echo "creating a different file for port configuration"
		. $PORTSTEMPLATE
	fi
}

mod_cmdb_gss () {
  echo ""
	echo "Creating a CMDB and GSS file. Directory:"
	. $CMDBGSSTEMPLATE
  echo -e "\t ${OUTPUTDIR}/"
}

case $SWITCHTYPE in
  access)
		mod_global
    mod_access
		mod_stack
		mod_finish
		mod_cmdb_gss
		mod_ports
		;;
  #L3)
		#mod_global
		#mod_stack
    #mod_L3
		#mod_finish
		#mod_cmdb_gss
		#mod_ports
		#;;
  #VSS)
		#mod_global
    #mod_VSS
		#mod_finish
		#;;
  *)
    echo "wrong choice, bye bye"
    exit;;
esac
