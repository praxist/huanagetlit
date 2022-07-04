#!/usr/bin/env sh
kill `cat /tmp/wd_pid`
# pipenv run -- bp -s --loglevel frame strips.local.yml &
pipenv run -- bp -s strips.local.yml &
echo "$!" > /tmp/wd_pid
