.PHONY: install test sandbox clean update-requirements

install:
	pip install -e .[test]

test:
	./runtests.py

sandbox: install
	pip install -r requirements.sandbox.txt
	-rm sandbox/db.sqlite
	sandbox/manage.py migrate
	sandbox/manage.py loaddata sandbox/fixtures/users.json

clean:
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov *.egg-info *.pdf dist

update-requirements:
	pip-compile requirements.sandbox.in || echo "\n\nPlease install pip-compile: pip install pip-tools"
