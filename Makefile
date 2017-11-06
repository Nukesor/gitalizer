default: venv

venv:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt -r requirements-dev.txt --upgrade

test: venv
	source ./local_env.sh && venv/bin/pytest

lint: venv
	source ./local_env.sh && venv/bin/flake8

clean:
	rm -rf venv
