#!/bin/bash

set -e



PY_ROOT=`pwd`



export PATH=$PY_ROOT/pythonroot-${PYTHON_VERSION}/bin:$PY_ROOT/pythonroot-${PYTHON_VERSION}/local/bin/:$PATH
export LD_LIBRARY_PATH=$PY_ROOT/pythonroot-${PYTHON_VERSION}/lib64:$LD_LIBRARY_PATH


rm -rf venv-${PYTHON_VERSION}

python3 -m venv venv-${PYTHON_VERSION}


pushd venv-${PYTHON_VERSION}

. ./bin/activate 

whereis pip3

# install base list
pip3 install -r ../requirements.txt

pip3 check

popd



