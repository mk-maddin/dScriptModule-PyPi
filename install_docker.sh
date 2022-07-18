#!/usr/bin/env bash
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: setup the current module from local system using pip

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#module="$(basename $( dirname "${BASH_SOURCE[0]}" ))"
module='dScriptModule'
docker_c="homeassistant"

echo "I: execute compile script local machine for: ${module}"
if [ ! -e  "${scriptDir}/compile.sh" ];then
	echo "error: cannot find compile script: ${scriptDir}/compile.sh"
	exit 2;fi
if [ "${UID}" -ne 0 ];then
    sudo source "${scriptDir}/compile.sh"
else
    source "${scriptDir}/compile.sh"
fi

echo "I: execute docker upload & install: ${module}"
if [ "${UID}" -ne 0 ];then
    sudo docker cp "${scriptDir}" "${docker_c}:/mnt/${module}" &&
        sudo docker exec "${docker_c}" bash -c "ls -la \"/mnt/\"" &&
        #sudo docker exec "${docker_c}" bash -c "cd \"/mnt/${module}\" && pip3 install dist/${module}-*-py3-none-any.whl"
        sudo docker exec "${docker_c}" bash -c "cd \"/mnt/${module}\" && chmod u+x \"/mnt/${module}/install.sh\" && \"/mnt/${module}/install.sh\""
    sudo docker exec "${docker_c}" rm -rf "/mnt/${module}"
else
    docker cp "${scriptDir}" "${docker_c}:/mnt/${module}" &&
        docker exec "${docker_c}" bash -c "ls -la \"/mnt/\"" &&
        #docker exec "${docker_c}" bash -c "cd \"/mnt/${module}\" && pip3 install dist/${module}-*-py3-none-any.whl"
        docker exec "${docker_c}" bash -c "cd \"/mnt/${module}\" && chmod u+x \"/mnt/${module}/install.sh\" && \"/mnt/${module}/install.sh\""
    docker exec "${docker_c}" rm -rf "/mnt/${module}"
fi

echo "I: script complete"
