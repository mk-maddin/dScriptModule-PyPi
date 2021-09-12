#!/bin/bash
# version: 2021.09.11
# description: manually copy and install the dScriptModule to HA server for test

##-- save maximum error code
error=0; trap 'error=$(($?>$error?$?:$error))' ERR

##--meta-information required paramteres
scriptAuthor="Martin Kraemer, mk.maddin@gmail.com"
scriptName=$( basename "$0" )
scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

##--default values for parameters
SSH_host="192.168.33.12"
SSH_pass='12345678'
SSH_user="root"
verbose=""
folder=$(dirname $(dirname "$scriptDir"))
ha_path="/usr/share/hassio/homeassistant"

##--help text and script parameter processing
for i in "$@";do
case $i in
	-h|--help) #help parameter for command
	echo ""
	echo "$scriptName" 
	echo "by $scriptAuthor" 
	echo ""
	echo "Usage: $scriptName [parameter]=[value]"
	echo ""
	echo "Parameter:"
	echo -e "\t -h \t| --help \t\t-> shows this help information"
	echo -e "\t -v \t| --verbose \t\t-> enable verbose ouput"
	echo -e "\t -f= \t| --folder= \t\t-> defines the folder to perform selected action on (default is: $folder)"
	echo -e "\t -h= \t| --host= \t\t-> hostname/IP-address of host to perform mode on (default is: $SSH_host)"
	echo -e "\t -u= \t| --user= \t\t-> username for ssh access to remote host (default is: $SSH_user)"
	echo -e "\t -p=  \t| --pass= \t\t-> password for ssh access to remote host (default is: $SSH_pass)"
	echo -e ""
	echo ""
	echo "Description:"
	echo "Manually copy and install this module to a home assistant server with docker installation"
	echo ""
	exit 0;;
	-v|--verbose)
	verbose="-v"
	shift;;
	-f=*|--folder=*)
	folder="${i#*=}"
	shift;;
	-h=*|--host=*)
	SSH_host="${i#*=}"
	shift;;
	-u=*|--user=*)
	SSH_user="${i#*=}"
	shift;;
	-p=*|--pass=*)
	SSH_pass="${i#*=}"
	shift;;
	*)  # unknown option
	>&2 echo "$scriptName: error: invalid option: $i" 
	>&2 echo "Try '$scriptName --help' for more information."
	exit 22;;
esac;done

echo "I: copy: ${folder}"
"${folder}/compile.sh" && 
	 sshpass -p "$SSH_pass"	scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r "${folder}" "${SSH_user}@${SSH_host}:${ha_path}/"

sshpass -p "$SSH_pass" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${SSH_user}@${SSH_host}" << EOF
	docker exec "homeassistant" chmod u+x /config/$(basename ${folder})/uninstall.sh && 
	docker exec "homeassistant" /config/$(basename ${folder})/uninstall.sh && 
	docker exec "homeassistant" chmod u+x /config/$(basename ${folder})/install.sh && 
	docker exec "homeassistant" /config/$(basename ${folder})/install.sh

	rm -rf "${ha_path}/$(basename ${folder})"
EOF


exit "$error"
