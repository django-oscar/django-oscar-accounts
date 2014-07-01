install:
	pip install -r requirements.testing.txt
	./setup.py develop 

test:
	./runtests.py

sandbox: install
	pip install -r requirements.sandbox.txt
	-rm sandbox/db.sqlite
	sandbox/manage.py syncdb --noinput
	sandbox/manage.py migrate
	sandbox/manage.py loaddata sandbox/fixtures/users.json countries.json

standalone: install
	pip install -r requirements.sandbox.txt
	-rm sandbox/db.sqlite
	sandbox/manage.py syncdb --settings=settings_standalone --noinput
	sandbox/manage.py migrate --settings=settings_standalone 


clean:
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov *.egg-info *.pdf dist 
