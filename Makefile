.PHONY: install test sandbox clean

install:
	pip install -e . -r requirements.txt

test:
	./runtests.py

sandbox: install
	-rm sandbox/db.sqlite
	sandbox/manage.py migrate
	sandbox/manage.py loaddata sandbox/fixtures/*.json
	sandbox/manage.py oscar_import_catalogue sandbox/fixtures/catalogue.csv
	sandbox/manage.py oscar_accounts_init

clean:
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov *.egg-info *.pdf dist

release:
	pip install twine wheel
	rm -rf dist/*
	python setup.py sdist bdist_wheel
	twine upload dist/*
