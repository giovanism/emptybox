import urllib3
import boto3
import click
import uuid
import json
import cgi
import io
import os
from flask import Flask, redirect, request
from flask.cli import with_appcontext

# Settings
app = Flask(__name__)
MAIN_SITE = os.getenv('EMPTYBOX_SITE', 'http://localhost:3000/')
S3_HOST = os.getenv('EMPTYBOX_S3_HOST')
S3_BUCKET = os.getenv('EMPTYBOX_S3_BUCKET')
S3_ACCESS_KEY = os.getenv('EMPTYBOX_S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('EMPTYBOX_S3_SECRET_KEY')

s3 = boto3.client('s3', endpoint_url=f'http://{S3_HOST}/',
                  aws_access_key_id=S3_ACCESS_KEY,
                  aws_secret_access_key=S3_SECRET_KEY)


# Utils

def gen_key(filename):
    '''
    Generate UUID4 based S3 key. The generated key also account for file
    extension for convenience.
    >>> get_key('anime.png')
    'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.png'
    >>> get_key('citra.JPG')
    'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.JPG'
    >>> get_key('.zshrc')
    'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.zshrc'
    >>> get_key('Dockerfile')
    'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    >>> get_key('')
    'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    >>> get_key(None)
    'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    '''
    if filename:
        root, ext = os.path.splitext(filename)

        if ext:
            return str(uuid.uuid4()) + ext

        elif root[0] == '.':
            return str(uuid.uuid4()) + root

    return str(uuid.uuid4())


# Handlers

@app.route('/')
def handle_default():
    return redirect(MAIN_SITE)


@app.route('/upload', methods=['POST'])
def upload():
    try:
        if request.form['type'] == 'file':
            file = request.files['file']
            body = file.stream
            filename = file.filename

        elif request.form['type'] == 'url':
            url = request.form['url']
            pool = urllib3.connection_from_url(url)
            response = pool.request('GET', url)
            body = io.BytesIO(response.data)

            filename = None

            if 'Content-Disposition' in response.headers:
                content_disposition = response.headers['Content-Disposition']
                value, params = cgi.parse_header(content_disposition)

                filename = params.get('filename')

        else:
            raise KeyError

    except KeyError as err:
        app.logger.debug(err)
        err = 'Invalid request'

        data = {'msg': err}
        return data, 400

    key = gen_key(filename)

    response = s3.put_object(Bucket=S3_BUCKET,
                             Key=key,
                             Body=body)

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        app.logger.info(response)
        return 'Error', 400

    return {'msg': 'Saved', 'filename': key}


@app.route('/stats')
def stats():
    response = s3.list_objects_v2(Bucket=S3_BUCKET)

    return {'fileCount': response['KeyCount']}


# Scripts

@click.command('init_bucket')
@with_appcontext
def init_bucket():
    '''
    Initialize the bucket used for the application.
    '''
    s3.create_bucket(Bucket=S3_BUCKET)

    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            'Resource': f'arn:aws:s3:::{S3_BUCKET}/*'
        }]
    }

    bucket_policy = json.dumps(bucket_policy)
    s3.put_bucket_policy(Bucket=S3_BUCKET, Policy=bucket_policy)

    click.echo('Successfully initialized bucket')


app.cli.add_command(init_bucket)
