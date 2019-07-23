import boto3
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


@app.route('/')
def handle_default():
    return redirect(MAIN_SITE)


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' in request.files:
        file = request.files['file']

        response = s3.put_object(Bucket=S3_BUCKET,
                                 Key=file.filename,
                                 Body=file.stream)

        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            app.logger.info(response)
            return 'Error', 400
        else:
            return 'Saved'

    else:
        err = 'No file provided'
        app.logger.debug(err)

        return err, 400


@app.route('/stats')
def stats():
    response = s3.list_objects_v2(Bucket=S3_BUCKET)

    data = {'fileCount': response['KeyCount']}
    return data
