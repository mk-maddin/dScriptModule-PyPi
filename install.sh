#!/usr/bin/env bash
# version: 2021.09.11
# author: Martin Kraemer, mk.maddin@gmail.com
# description: setup the current module from local system using pip

scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#module="$(basename $( dirname "${BASH_SOURCE[0]}" ))"
module='dScriptModule'

echo "I: install on local machine: ${module}"
if [ "${UID}" -ne 0 ];then
	#cd "${scriptDir}" && sudo pip3 install --force dist/${module}-*-py3-none-any.whl
    #cd "${scriptDir}" && sudo pip3 install --proxy='http://frankfurt.proxy.knaufgroup.com:10129/' --force dist/${module}-*-py3-none-any.whl    
    #cd "${scriptDir}" && sudo pip3 install --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --force dist/${module}-*-py3-none-any.whl
    cd "${scriptDir}" && sudo pip3 install --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --proxy='http://frankfurt.proxy.knaufgroup.com:10129/' --force dist/${module}-*-py3-none-any.whl
else
	#cd "${scriptDir}" && pip3 install --force dist/${module}-*-py3-none-any.whl
    #cd "${scriptDir}" && pip3 install --proxy='http://frankfurt.proxy.knaufgroup.com:10129/' --force dist/${module}-*-py3-none-any.whl
    #cd "${scriptDir}" && pip3 install --trusted-host=pypi.org --trusted-host=files.pythonhosted.org  --force dist/${module}-*-py3-none-any.whl
    cd "${scriptDir}" && pip3 install --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --proxy='http://frankfurt.proxy.knaufgroup.com:10129/' --force dist/${module}-*-py3-none-any.whl
fi

echo "I: script complete"
