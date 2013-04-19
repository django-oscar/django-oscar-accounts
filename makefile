install:
	pip install -r requirements.txt --use-mirrors
	./setup.py develop 

test:
	./runtests.py

sandbox: install
	-rm sandbox/db.sqlite
	sandbox/manage.py syncdb --noinput
	sandbox/manage.py loaddata sandbox/fixtures/users.json countries.json

clean:
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov *.egg-info *.pdf dist 
