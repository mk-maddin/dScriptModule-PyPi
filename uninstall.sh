#!/usr/bin/env bash
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: remove the module from the local system using pip (by package name - no version / wheel file needed)

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#module="$(basename $( dirname "${BASH_SOURCE[0]}" ))"
module='dScriptModule'

echo "I: uninstall from local machine: ${module}"
if [ "${UID}" -ne 0 ];then
	sudo pip3 uninstall -y "${module}"
else
	pip3 uninstall -y "${module}"
fi

echo "I: script complete"
