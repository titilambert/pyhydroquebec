env:
	virtualenv -p `which python3.9` env
	env/bin/pip install -r requirements.txt
	env/bin/pip install -r test_requirements.txt
	env/bin/python setup.py develop

upload:
	env/bin/python setup.py sdist upload -r pypi


docker-mqtt:
	docker build -t pyhydroquebec:mqtt-heehoo .

docker-cli:
	docker build -t pyhydroquebec:heehoo .
