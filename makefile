install:
	./setup.py develop
	pip install -r requirements.txt

test:
	./runtests.py

sandbox: install
	sandbox/manage.py syncdb --noinput
	sandbox/manage.py loaddata sandbox/fixtures/users.json
