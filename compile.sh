#!/usr/bin/env bash
# version: 2020.06.14
# author: Martin Kraemer, mk.maddin@gmail.com
# description: setup the current module from local system using pip

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#module="$(basename $( dirname "${BASH_SOURCE[0]}" ))"
module='dScriptModule'

pip3 install bitstring

echo "I: compile package ${module}"
cd "${scriptDir}" && python3 setup.py bdist_wheel

#echo "I: upload to pypi: ${module}"
#cat > "$HOME/.pypirc" <<EOF
#[distutils] 
#index-servers=pypi
#[pypi] 
#repository = https://upload.pypi.org/legacy/ 
#username = mk-maddin
#EOF
#cd "${scriptDir}" && python3 -m twine upload dist/*

echo "I: script complete"
