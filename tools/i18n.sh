#!/bin/sh

pybabel extract -F babel.cfg \
    -k __ -k _ -k gettext -k ngettext -k lazy_gettext \
    --msgid-bugs-address=hieulq19@gmail.com \
    --copyright-holder="Hieu LE" \
    --project="PGSCM" \
    --version="1.0.0" \
    -o pgscm/translations/messages.pot .

#pybabel update -i pgscm/translations/messages.pot -l vi -d pgscm/translations/
#pybabel compile -d pgscm/translations/