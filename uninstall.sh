#!/usr/bin/env bash
# version: 2018.10.05
# author: Martin Kraemer, mk.maddin@gmail.com
# description: setup the current module from local system using pip

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
module="$(basename $( dirname "${BASH_SOURCE[0]}" ))"
version='1.4' #this has to match setup.py version

echo "I: uninstall from local machine: ${module}"
if [ "${UID}" -ne 0 ];then
	cd "${scriptDir}" && sudo pip3 uninstall -y dist/${module}-*-py3-none-any.whl
else
	cd "${scriptDir}" && pip3 uninstall -y dist/${module}-*-py3-none-any.whl
fi

echo "I: script complete"
