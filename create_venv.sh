#!/bin/sh -ex
python3 -m venv ./venv
./venv/bin/pip3 install \
'python-telegram-bot[job-queue]' \
wolframalpha \
cryptography \
mysql-connector-python
