#!/usr/bin/env bash

cp -i WhatManager2/user_settings.example.py WhatManager2/user_settings.py

sudo apt install -y python3-pip flac lame sox mktorrent curl python3-dev libssl-dev

sudo pip3 install pipenv
export PIPENV_VENV_IN_PROJECT=True
pipenv install --three

sudo chmod 777 media/book_data
sudo chmod 777 media/what_image_cache
sudo chmod 777 media/qobuz_uploads