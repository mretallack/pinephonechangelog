
# Rule to make Python
pythonroot-${PYTHON_VERSION}/bin/python3:
	./compilePython.sh




# Rule to setup teh venv for pythin
venv-${PYTHON_VERSION}/bin/activate: pythonroot-${PYTHON_VERSION}/bin/python3 ./requirements.txt
	./setupPython.sh


# rule to setup python
setupEnv: venv-${PYTHON_VERSION}/bin/activate


.PHONY: setupEnv update

