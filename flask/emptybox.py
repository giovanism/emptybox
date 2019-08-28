import urllib3
import boto3
import uuid
import io
import os
from flask import Flask, redirect, request
from PIL import Image

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

def gen_filename(fmt):
    return f'{uuid.uuid4()}.{fmt.lower()}'


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

        elif request.form['type'] == 'url':
            url = request.form['url']
            pool = urllib3.connection_from_url(url)
            response = pool.request('GET', url)
            body = io.BytesIO(response.data)

        else:
            raise KeyError

    except KeyError:
        err = 'Invalid request'
        app.logger.debug(err)

        return err, 400

    img = Image.open(body)
    key = gen_filename(img.format)

    body.seek(0)

    response = s3.put_object(Bucket=S3_BUCKET,
                             Key=key,
                             Body=body)

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        app.logger.info(response)
        return 'Error', 400

    return 'Saved'


@app.route('/stats')
def stats():
    response = s3.list_objects_v2(Bucket=S3_BUCKET)

    data = {'fileCount': response['KeyCount']}
    return data
