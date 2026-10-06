#!/usr/bin/env bash
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: setup the current module from local system using pip

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#module="$(basename $( dirname "${BASH_SOURCE[0]}" ))"
module='dScriptModule'
version="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "${scriptDir}/${module}/__init__.py")" # read from the package, never maintain it here
# current setuptools write the wheel name in lower case (dscriptmodule-x.y.z-...) - match both spellings
wheel="$(ls "${scriptDir}"/dist/[dD][sS]cript[mM]odule-"${version}"-py3-none-any.whl 2>/dev/null | head -n 1)"
if [ -z "${wheel}" ];then
	echo "error: cannot find wheel for version ${version} in ${scriptDir}/dist - run compile.sh first"
	exit 2;fi

echo "I: install on local machine: ${module} ${version} (${wheel})"
if [ "${UID}" -ne 0 ];then
	cd "${scriptDir}" && sudo pip3 install --force "${wheel}"
else
	cd "${scriptDir}" && pip3 install --force "${wheel}"
fi

echo "I: script complete"
