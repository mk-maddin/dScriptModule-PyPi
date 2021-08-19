#! /bin/bash

while [ 1 == 1 ];do
	echo -e '\xff' | nc -w 5 192.168.33.12 17123 && echo 'true' || echo 'false'
	sleep 1
done
