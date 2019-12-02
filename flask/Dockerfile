FROM kennethreitz/pipenv:latest

WORKDIR /tmp
COPY Pipfile Pipfile.lock ./
RUN ["pipenv", "install"]
RUN pipenv run pip freeze | tee requirements.txt

FROM python:3.7-alpine
WORKDIR /opt
COPY --from=0 /tmp/requirements.txt ./
RUN ["pip", "install", "-r", "requirements.txt"]
COPY emptybox.py ./

ENV FLASK_APP=emptybox.py
EXPOSE 8000

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "emptybox:app"]
