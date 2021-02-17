import logging
import boto3
from config import read_config, validate_config
import os.path
from botocore.exceptions import ClientError

def upload_file(config,path,file_name):

    # Upload the file
    aws_config = config['aws']
    s3 = getBotoResource(aws_config)
    table = aws_config['table']
    bucket = s3.Bucket(aws_config['bucket'])
    aws_name = f'{table}/i{file_name.replace("_","/")}'


    try:

        full_path = os.path.join(path,file_name)
        response = bucket.upload_file(full_path, aws_name)
        print(f'awsUpload {file_name}, response: {response}')

    except Exception as e:
        print(f'Aws connector: {e}')
        return False    
    return True

def getBotoResource(aws_config):

    return boto3.resource( 's3',
                            aws_access_key_id = aws_config['key_id'],
                            aws_secret_access_key = aws_config['key'],
                            region_name = aws_config['region'] )

# TEST code 
if  __name__ == "__main__":
    config = read_config()
    if validate_config(config) == False:
        quit()

    aws_config = config['aws']

    bucket_name = aws_config['bucket']
    s3 = getBotoResource(aws_config)
    if s3 == None:
        quit()

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