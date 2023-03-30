# ckan-xsearch

- Install

Download Solr from the official site and install it.

```
curl -SL https://ftp.jaist.ac.jp/pub/apache/lucene/solr/8.7.0/solr-8.7.0.tgz \
| tar xfz -
./solr-8.7.0/bin/solr start -p 8983
./solr-8.7.0/bin/solr create -c ckan-xsearch -p 8983
./solr-8.7.0/bin/solr config -c ckan-xsearch -p 8983 \
  -action set-user-property \
  -property update.autoCreateFields \
  -value false
curl -X POST -H 'Content-type:application/json' \
  --data-binary @xckan-schema.json \
  http://localhost:8983/solr/ckan-xsearch/schema
```

Then, install this (ckan-xsearch) package using pipenv.

```
pip install pipenv
pipenv install
```

- Configure

Edit `xckan/siteconf.py`.

If you want to change the logging settings, edit `xckan/logging.json` also.

- Migrate database

The first time and if you change the database model,
you will need to update the database.

```shell
python django-backend/manage.py makemigrations
python django-backend/manage.py migrate
```

- Create administrator account

For the first time, you will need to create an administrator account.

```shell
python django-backend/manage.py createsuperuser
username: xckan
email: xckan@search.jp
Password: xckan
Password (again): xckan
Superuser created successfully.
```

- Start backend server

```
python django-backend/manage.py runserver '0.0.0.0:8000'
```

or run pipenv script as follows:
```
pipenv run start
```

- Access administration site

Open http://localhost:8000/admin/ in a browser.


- Start a new harvesting process

```shell
python django-backend/manage.py runscript update
```
or run pipenv script as follows:
```
pipenv run updatemetadata
```
