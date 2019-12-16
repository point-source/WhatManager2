#!/usr/bin/env bash

cp -i WhatManager2/user_settings.example.py WhatManager2/user_settings.py

apt install -y python3-pip flac lame sox mktorrent curl python3-dev libssl-dev

pip3 install pipenv
export PIPENV_VENV_IN_PROJECT=True
pipenv install --three

chmod 777 -R media