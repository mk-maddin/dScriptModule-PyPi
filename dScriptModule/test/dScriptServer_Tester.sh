#! /bin/bash

server=$1
port=$2

if [ -z "${server}" ];then server=192.168.33.12;fi
if [ -z "${port}" ];then port=17123;fi

while [ 1 == 1 ];do
	echo -e '\xff' | nc -w 5 $server $port && echo 'true' || echo 'false'
	sleep 1
done
