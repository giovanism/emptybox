import urllib3
import boto3
import uuid
import cgi
import io
import os
from flask import Flask, redirect, request

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
            return f'{uuid.uuid4()}.{ext}'

        elif root[0] == '.':
            return f'{uuid.uuid4()}.{root}'

    return  str(uuid.uuid4())


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

    except KeyError:
        err = 'Invalid request'
        app.logger.debug(err)

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
