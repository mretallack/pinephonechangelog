


PYTHON_VERSION=3.8.3


export PYTHON_VERSION


PY_ROOT=python/pythonroot-${PYTHON_VERSION}

export PATH:=bin:$(PY_ROOT)/bin:$(PY_ROOT)/local/bin/:$(PATH)
export LD_LIBRARY_PATH:=$(PY_ROOT)/lib64:$(LD_LIBRARY_PATH)

python/venv-${PYTHON_VERSION}/bin/activate:
	${MAKE} -C python setupEnv


diff: python/venv-${PYTHON_VERSION}/bin/activate e2tools/e2tools
	@. python/venv-${PYTHON_VERSION}/bin/activate ; python3 diff.py


e2tools/e2tools:
	rm -fr e2tools
	git clone https://github.com/e2tools/e2tools.git
	cd e2tools && autoreconf -i && ./configure && make
    

shell:
	bash --init-file python/venv-${PYTHON_VERSION}/bin/activate
