#!/usr/bin/env bash
# version: 2018.10.05
# author: Martin Kraemer, mk.maddin@gmail.com
# description: setup the current module from local system using pip

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
module="$(basename $( dirname "${BASH_SOURCE[0]}" ))"

echo "I: setup module ${module} from ${scriptDir}"
sudo pip3 install "${module}" --no-index --find-links "file://${scriptDir}"

echo "I: setup complete"
