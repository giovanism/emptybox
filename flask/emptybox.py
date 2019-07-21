import hmac
import os
import time

from binascii import b2a_base64
from email.utils import formatdate
from http.client import HTTPConnection
from flask import Flask, redirect, request

# Settings
app = Flask(__name__)
MAIN_SITE = os.getenv('EMPTYBOX_SITE', 'http://localhost:3000/')
S3_HOST = os.getenv('EMPTYBOX_S3_HOST')
S3_BUCKET = os.getenv('EMPTYBOX_S3_BUCKET')
S3_ACCESS_KEY = os.getenv('EMPTYBOX_S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('EMPTYBOX_S3_SECRET_KEY')


@app.route('/')
def handle_default():
    return redirect(MAIN_SITE)


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' in request.files:
        file = request.files['file']
        date = formatdate(time.time())
        resource = f'/{S3_BUCKET}/{file.filename}'
        content_type = 'application/octet-stream'

        to_sign = f'PUT\n\n{content_type}\n{date}\n{resource}'
        bytes_to_sign = bytearray(to_sign, 'utf-8')
        secret_bytes = bytearray(S3_SECRET_KEY, 'utf-8')
        signature_bytes = hmac.digest(secret_bytes, bytes_to_sign, 'sha256')
        signature_b64_bytes = b2a_base64(signature_bytes, newline=False)
        signature = signature_b64_bytes.decode('utf-8')

        conn = HTTPConnection(S3_HOST)
        conn.request('PUT', resource, body=file.stream,
                     headers={
                         'Host': f'{S3_BUCKET}.{S3_HOST}',
                         'Date': date,
                         'Content-Type': content_type,
                         'Content-Length': file.content_length,
                         'Authorization':
                             f'AWS4-HMAC-256 {S3_ACCESS_KEY}:{signature}'})

        response = conn.getresponse()

        if response.status == 200:
            return 'Saved'
        else:
            err = response.read()
            app.logger.debug(err)

            return err, response.status

    else:
        err = 'No file provided'
        app.logger.debug(err)

        return err, 400


@app.route('/stats')
def stats():
    data = {'fileCount': 0}
    return data
