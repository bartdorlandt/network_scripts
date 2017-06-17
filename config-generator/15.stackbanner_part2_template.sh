#!/bin/bash
#echo STACKAMOUNT = $STACKAMOUNT
i="1"
j="1"
k="1"
KEYAPPEND=""

cat >> $OUTPUTFILE << EOF
banner exec #
     ***************************************************************
     *******
     *******      Switch: \$(hostname).\$(domain)
     *******
     *******      Location: $VARSITEID, $VARCITYNAME
     *******
     *******      Cabinet : $VARBUILDING, $VARROOMNUMBER - $VARROOMALIAS
     *******
EOF

while [ $i -lt $STACKAMOUNT ] ; do
	echo "     *******      [$i]  Tag: $(eval echo $`echo TAG$i` | cut -d "W" -f2)   sn: $(eval echo $`echo SERIALNUMBER$i`)" >> $OUTPUTFILE
	i=$[$i+1]
done
#
echo "     *******" >> $OUTPUTFILE
#
while [ $j -lt $STACKAMOUNT ] ; do
	echo "     *******      [$j]  Model ID: $(eval echo $`echo HARDWARE$j`)" >> $OUTPUTFILE
	j=$[$j+1]
done
#
echo "     *******" >> $OUTPUTFILE
echo "     ***************************************************************" >> $OUTPUTFILE
echo "#" >> $OUTPUTFILE
echo "!" >> $OUTPUTFILE
echo "!" >> $OUTPUTFILE

if [ ! -n "`echo $HARDWARE1 | grep C3650`" ] ; then
	# Switch priority configuration
	SWPRIORITY="15"
	# Provision needs to be written still
	while [ $k -lt $STACKAMOUNT ] ; do
  	echo "switch $k priority $SWPRIORITY" >> $OUTPUTFILE
  	echo "" >> $OUTPUTFILE
  	k=$[$k+1]
  	SWPRIORITY=$[$SWPRIORITY-2]
	done
else
  SWPRIORITY="15"
  # Provision needs to be written still
  while [ $k -lt $STACKAMOUNT ] ; do
    echo "do switch $k priority $SWPRIORITY" >> $OUTPUTFILE
    echo "" >> $OUTPUTFILE
    k=$[$k+1]
    SWPRIORITY=$[$SWPRIORITY-2]
  done
fi
echo "!" >> $OUTPUTFILE
echo "!" >> $OUTPUTFILE

