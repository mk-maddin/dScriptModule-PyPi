#!/usr/bin/env bash
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: setup the current module from local system using pip

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#module="$(basename $( dirname "${BASH_SOURCE[0]}" ))"
module='dScriptModule'

echo "I: compile package ${module}"
if [ "${UID}" -ne 0 ];then
    cd "${scriptDir}" &&
    sudo pip3 install bitstring &&
    sudo pip3 install pycryptodome &&
    sudo python3 setup.py sdist bdist_wheel
else
    cd "${scriptDir}" &&
    pip3 install bitstring &&
    pip3 install pycryptodome &&
    python3 setup.py sdist bdist_wheel
fi

echo "I: upload to pypi: ${module}"
cd "${scriptDir}" && 
	pip3 install twine && 
	python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

echo "I: for productive upload execute:"
echo "   python3 -m twine upload dist/*"

echo "I: script complete"
