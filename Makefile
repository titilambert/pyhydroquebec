env:
	python setup.py develop
	virtualenv -p /usr/bin/python3.5 env
	pip install -r requirements.txt
	pip install -r test_requirements.txt

upload:
	python setup.py sdist upload -r pypi

test:
	tox
