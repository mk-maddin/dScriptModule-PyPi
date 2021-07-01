#!/usr/bin/env bash
# version: 2020.06.22
# author: Martin Kraemer, mk.maddin@gmail.com
# description: setup the current module from local system using pip

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#module="$(basename $( dirname "${BASH_SOURCE[0]}" ))"
module='dScriptModule'

if [ ! -e  "${scriptDir}/install.sh" ];then
	echo "error: cannot find install script: ${scriptDir}/install.sh"
	exit 2;fi
source "${scriptDir}/install.sh"

echo "I: execute test"
#sudo python3 "${scriptDir}/${module}/test/dScriptServer_InteractiveTest.py"
#sudo python3 "${scriptDir}/${module}/test/dScriptBoard_InteractiveTest_Binary.py"
sudo python3 "${scriptDir}/${module}/test/dScriptBoard_InteractiveTest_BinaryAES.py"

echo "I: script complete"
