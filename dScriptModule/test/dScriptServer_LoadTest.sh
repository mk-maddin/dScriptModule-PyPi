#!/bin/bash
# version: 2019.12.29
# description: starts a dScriptServer and simulates a high number of connections to this server

##-- save maximum error code
error=0; trap 'error=$(($?>$error?$?:$error))' ERR

##--meta-information required paramteres
scriptAuthor="Martin Kraemer, mk.maddin@gmail.com"
scriptName=$( basename "$0" )
scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sh="${scriptDir}/../../uninstall.sh"
chmod u+x "${sh}" && "${sh}"

sh="${scriptDir}/../../compile.sh"
chmod u+x "${sh}" && "${sh}"

sh="${scriptDir}/../../install.sh"
chmod u+x "${sh}" && "${sh}"

py="${scriptDir}/dScriptServer_InteractiveTest.py"
x-terminal-emulator -T Server -e "python3 ${py}"
sleep 3

py="${scriptDir}/dScriptVirtualBoard_LoadTest.py"
python3 ${py}

exit "$error"
