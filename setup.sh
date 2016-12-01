#!/usr/bin/env bash
sudo apt-get install -y libapache2-mod-wsgi python-pip flac lame sox libmysqlclient-dev python-dev libxml2-dev libxslt1-dev curl

sudo git clone https://github.com/Rudde/mktorrent.git
cd ./mktorrent/
sudo make
sudo make install
cd ../
sudo rm -r ./mktorrent

sudo pip install -r requirements.txt
sudo chmod 777 media/book_data
sudo chmod 777 media/what_image_cache
