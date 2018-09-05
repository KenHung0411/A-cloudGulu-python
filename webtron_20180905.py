import boto3
import click
# to handle boto3 exception
from botocore.exceptions import ClientError
from pathlib import Path
import mumetypes

session = boto3.Session(profile_name='pythonAutomation')
s3 = session.resource('s3')

@click.group()
def cli():
    """Webotron deploys website to AWS"""
    pass

@cli.command('list-buckets')
def list_buckets():
    """List All S3 buckets"""
    for bucket in s3.buckets.all():
        print(bucket)

@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List objects in an S3 bucket"""
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)

@cli.command('setup-bucket')
@click.argument('bucket_name')
def setup_bucket(bucket_name):
    try:
        "Create and configure S3 bucket"
        new_bucket = s3.create_bucket(Bucket= bucket_name, CreateBucketConfiguration={'LocationConstraint': session.region_name})
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
        else:
            raise e

    #set bucket policy
    policy = """{
      "Version":"2012-10-17",
      "Statement":[
        {
          "Sid":"AddPerm",
          "Effect":"Allow",
          "Principal": "*",
          "Action":["s3:GetObject"],
          "Resource":["arn:aws:s3:::%s/*"]
        }
      ]
    }""" % new_bucket.name

    bucket_policy = new_bucket.Policy()
    bucket_policy.put(Policy=policy)

    #set website configuration
    ws = new_bucket.Website()
    ws.put(WebsiteConfiguration={ 'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }})

def upload_file(s3_bucket, path, key):
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    s3_bucket.upliad_file(path, key, ExtraArgs={'ContentType':content_type})



@cli.command('sync')
@click.argument('pathname', type = click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to BUCKET"""
    s3_bucket = s3.Bucket(bucket)

    root = Path(pathname).expanduser()
    print(root)

    def handle_directory(target):
      for p in target.iterdir():
          if p.is_dir():
              #recursive
              handle_directory(p)
          if p.is_file():
              upload_file(s3_bucket, str(p), str(p.relative_to(root)))
              print("Path: {}\n Key: {}".format(p, p.relative_to(root)))

    handle_directory(root)

if __name__ == "__main__":
    cli()
