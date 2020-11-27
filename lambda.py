import boto3
from botocore.errorfactory import ClientError
import json
import os

from io import BytesIO
import PIL
from PIL import Image

import csv
from requests import get

class Bucket():
    def __init__(self, prefix, name, suffix):
        self.bucket_name = f'{prefix}{name}{suffix}'

    def __str__(self):
        return self.bucket_name

class ImageAWS():

    def __init__(self, src, bucket_name, path, dst_name):
        response = get(src)
        self.bucket = bucket_name
        self.path = path

        self.image = PIL.Image.open(BytesIO(response.content))
        file_name, self.file_extension = os.path.splitext(src)
        self.dst_name = dst_name

    def path_section(self, suffix):
        self.path_section = suffix

    def save(self, folder, size):
        file_name = self.dst_name + self.file_extension.lower() 
        key = f'{self.path}/{folder}{file_name}'

        try:
            s3 = boto3.client('s3')
            objs = s3.head_object(Bucket=self.bucket, Key=key)
        except ClientError:
            dst = boto3.resource('s3')
            bucket = dst.Bucket(self.bucket)

            file_stream = self.image
            fstream = BytesIO()
            file_stream.thumbnail(size)

            if self.file_extension[1:].upper() == 'JPG':
                mime_type = 'JPEG'
            else:
                mime_type = self.file_extension[1:].upper()

            file_stream.save(fstream, mime_type, optimize=True)
            tmp = bucket.Object(key)
            txt = tmp.put(ACL='public-read', Body=fstream.getvalue())

            return txt

def lambda_handler(event, context):
    thumbnail_size = (64, 64)
    small_size = (200, 200)
    default_size = (350, 350)
    large_size = (1000, 1000)

    body = json.loads(event['body'])

    if type(body) is list: 
        for img in body:
            bucket = Bucket(img['bucket_prefix'], img['bucket_name'], img['bucket_suffix'])
            product_id = img['product_id']
            path = f'products/{product_id}'
            image = ImageAWS(img['url'], str(bucket), path, img['name'])

            large_rsp = image.save('large/', large_size)
            print("<[RSP]> large ", large_rsp)
            default_rsp = image.save('', default_size)
            print("<[RSP]> default ", default_rsp)
            small_rsp = image.save('small/', small_size)
            print("<[RSP]> small ", small_rsp)
            thumbnail_rsp = image.save('thumbnail/', thumbnail_size)
            print("<[RSP]> thumbnail ", thumbnail_rsp)
      
        return f"[200]"
    else:
        return "[504]"

