#!/usr/bin/env bash
# version: 2020.06.14
# author: Martin Kraemer, mk.maddin@gmail.com
# description: setup the current module from local system using pip

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
module="$(basename $( dirname "${BASH_SOURCE[0]}" ))"

echo "I: install on local machine: ${module}"
if [ "${UID}" -ne 0 ];then
	cd "${scriptDir}" && sudo pip3 install --force dist/${module}-*-py3-none-any.whl
else
	cd "${scriptDir}" && pip3 install --force dist/${module}-*-py3-none-any.whl
fi

echo "I: script complete"
