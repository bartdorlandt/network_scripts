#!/bin/bash

if [ ! -f $1 ]; then
	echo "file $1 doesn't exists"
	exit
fi

FILE=`cat $1`
for x in $FILE; do
	case "$x" in 
		0.0.0.0)
			echo "/32"
			;;
		0.0.0.1)
			echo "/31"
			;;
		0.0.0.3)
			echo "/30"
			;;
		0.0.0.7)
			echo "/29"
			;;
		0.0.0.15)
			echo "/28"
			;;
		0.0.0.31)
			echo "/27"
			;;
		0.0.0.63)
			echo "/26"
			;;
		0.0.0.127)
			echo "/25"
			;;
		0.0.0.255)
			echo "/24"
			;;
		0.0.1.255)
			echo "/23"
			;;
		0.0.3.255)
			echo "/22"
			;;
		0.0.7.255)
			echo "/21"
			;;
		0.0.15.255)
			echo "/20"
			;;
		0.0.31.255)
			echo "/19"
			;;
		0.0.63.255)
			echo "/18"
			;;
		0.0.127.255)
			echo "/17"
			;;
		0.0.255.255)
			echo "/16"
			;;
		*)
			echo "nothing found"
			exit 1
	esac
done
