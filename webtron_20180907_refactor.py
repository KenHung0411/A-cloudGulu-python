#!/user/bin/python
# -*- codinf: urf-8 -*-

""" Webtron: Deploy websites with aws
    Webtron automates the process of deploying static websites to AWS.
    - Configure AWS S3 buckets
        - Create them
        - Set them up for static website hosting
    ...
"""


# to handle boto3 exception
from botocore.exceptions import ClientError
from pathlib import Path
import mimetypes

import boto3
import click


session = boto3.Session(profile_name='pythonAutomation')
s3 = session.resource('s3')


@click.group()
def cli():
    """Webotron deploys website to AWS."""
    pass


@cli.command('list-buckets')
def list_buckets():
    """List All S3 buckets"""
    for bucket in s3.buckets.all():
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List objects in an S3 bucket."""
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)


@cli.command('setup-bucket')
@click.argument('bucket_name')
def setup_bucket(bucket_name):
    try:
        """Create and configure S3 bucket."""
        new_bucket = s3.create_bucket(Bucket=bucket_name,
                                      CreateBucketConfiguration={'LocationConstraint':session.region_name})

    except ClientError as error:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
        else:
            raise error

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
    }""" % new_bucket.name

    bucket_policy = new_bucket.Policy()
    bucket_policy.put(Policy=policy)

    #set website configuration
    new_bucket.Website().put(WebsiteConfiguration={'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }})


def upload_file(s3_bucket, path, key):
    """Upload path to S3 bucket."""
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    s3_bucket.upload_file(path, key, ExtraArgs={'ContentType':content_type})


@cli.command('sync')
@click.argument('pathname', type = click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to BUCKET."""
    s3_bucket = s3.Bucket(bucket)

    root = Path(pathname).expanduser().resolve()
    print(root)

    def handle_directory(target):
      for path in target.iterdir():
          if path.is_dir():
              # recursive
              handle_directory(p)
          if path.is_file():
              upload_file(s3_bucket, str(p), str(p.relative_to(root)))
              print("Path: {}\n Key: {}".format(p, p.relative_to(root)))

    handle_directory(root)


if __name__ == "__main__":
    cli()
