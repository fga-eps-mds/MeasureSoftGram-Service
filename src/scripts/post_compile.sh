# !/usr/bin/env bash

# Script que é executado após o heroku compilar a versão deployada.

# File path should be ./bin/post_compile
# (.sh extension added in Gist just to enable shell syntax highlighting.
# https://discussion.heroku.com/t/django-automaticlly-run-syncdb-and-migrations-after-heroku-deploy-with-a-buildpack-or-otherwise/466/7

echo '======= RUNNING MIGRATIONS'
python3 manage.py migrate

echo '======= PREPOPULATING THE DATABASE'
python3 manage.py load_initial_data


