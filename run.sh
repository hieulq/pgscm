#!/bin/bash

#python3 manage.py runserver -h 0.0.0.0 -p 80 &
GUNICORN_CMD_ARGS="--daemon --bind=0.0.0.0:80 --workers=4 --access-logfile=pgs-acc.log --log-file=pgs-err.log --log-level DEBUG" gunicorn wsgi:app