install:
	./setup.py develop > /dev/null
	pip install -r requirements.txt > /dev/null

test:
	./runtests.py

sandbox: install
	[ -f sandbox/db.sqlite ] && rm sandbox/db.sqlite
	sandbox/manage.py syncdb --noinput > /dev/null
	sandbox/manage.py loaddata sandbox/fixtures/users.json countries.json > /dev/null
