import logging
import boto3
from botocore.exceptions import ClientError

keyId ='AKIAIDJGOCSLSCWMRH3A'
key = 'yRHRn5+nkACxQ7P8Lx0yTwY3N4pZahW5YM4adL3x'
bucket_name = 'kring-bucket-test'

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False    
    return True
    
# Creating the low level functional client
client = boto3.client(
    's3',
    aws_access_key_id = keyId,
    aws_secret_access_key = key,
    region_name = 'us-west-1'
)

# Creating the high level object oriented interface
s3 = boto3.resource(
    's3',
    aws_access_key_id = keyId,
    aws_secret_access_key = key,
    region_name = 'us-west-1'
)
bucket = s3.Bucket(bucket_name)
print(bucket)

print(dir(bucket))
try:
    bucket.upload_file('test.txt','test1.txt')
except Exception as e:
    print(f"Exception uploading file: {e}")
try:
    bucket.download_file('test1.txt','test2.txt')
except Exception as e:
    print(f"Exception uploading file: {e}")
# Print the bucket names one by one
#response = client.list_buckets() 
#for bucket in response['Buckets']:
    #print(f'Bucket Name: {bucket["Name"]}')
#
#bucket = client.get_bucket(bucket_name, validate=False)
#
#upload_file('test.txt', bucket )
