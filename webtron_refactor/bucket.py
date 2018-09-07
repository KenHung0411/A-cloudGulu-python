# -*- coding: utf-8 -*-
import mimetypes
from pathlib import Path
# to handle boto3 exception
from botocore.exceptions import ClientError


""" Classes for S3 Buckets."""

class BucketManager:
    """Manage sn S3 Bucket."""

    def __init__(self, session):
        """Create a bucket object."""
        self.session = session
        self.s3 = self.session.resource('s3')

    def all_buckets(self):
        """"Get an iterator for all buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):
        """Get an iterator for all objects."""
        return self.s3.Bucket(bucket_name).objects.all()

    def init_bucket(self, bucket_name):
        try:
            """Create and configure S3 bucket."""
            new_bucket = self.s3.create_bucket(Bucket=bucket_name,
                                          CreateBucketConfiguration={'LocationConstraint':session.region_name})

        except ClientError as error:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket)
            else:
                raise error

    def set_policy(self, bucket):
        """Set bucket policy to be readable by everyone."""
        #set bucket policy
        policy = """{
          "Version":"2012-10-17",
          "Statement":[
            {
              "Sid": "AddPerm",
              "Effect": "Allow",
              "Principal": "*",
              "Action": ["s3:GetObject"],
              "Resource": ["arn:aws:s3:::%s/*"]
            }
          ]
        }""" % bucket.name

        bucket_policy = bucket.Policy()
        bucket_policy.put(Policy=policy)

    def configure_website(self, bucket):
        #set website configuration
        bucket.Website().put(WebsiteConfiguration={'ErrorDocument': {
                'Key': 'error.html'
            },
            'IndexDocument': {
                'Suffix': 'index.html'
            }})

    @staticmethod
    def upload_file(bucket, path, key):
        """Upload path to S3 bucket."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        bucket.upload_file(path, key, ExtraArgs={'ContentType':content_type})

    def sync(self, pathname, bucket_name):
        root = Path(pathname).expanduser().resolve()
        print(root)

        def handle_directory(target):
          for path in target.iterdir():
              if path.is_dir():
                  # recursive
                  handle_directory(p)
              if path.is_file():
                  self.upload_file(s3_bucket, str(p), str(p.relative_to(root)))
                  print("Path: {}\n Key: {}".format(p, p.relative_to(root)))

        handle_directory(root)
