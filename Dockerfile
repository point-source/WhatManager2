FROM ubuntu:19.10

WORKDIR /whatmanager

RUN apt update \
  && apt install -y git flac lame sox mktorrent curl netcat \
  python3-pip python3-dev libssl-dev libmysqlclient-dev \
  && pip3 install pipenv

COPY ./Pipfile /whatmanager/Pipfile
COPY ./Pipfile.lock /whatmanager/Pipfile.lock
RUN pipenv install --system

COPY ./entrypoint.sh /whatmanager/entrypoint.sh

ENTRYPOINT [ "/whatmanager/entrypoint.sh" ]