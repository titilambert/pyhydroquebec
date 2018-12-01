env:
	virtualenv -p `which python3` env
	env/bin/pip install -r requirements.txt
	env/bin/pip install -r test_requirements.txt
	env/bin/python setup.py develop

upload:
	env/bin/python setup.py sdist upload -r pypi

test:
	env/bin/tox
