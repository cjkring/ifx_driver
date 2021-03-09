import logging
import boto3
from config import read_config, validate_config
import os.path
from botocore.exceptions import ClientError

def awsExport(config, filename):

    # Upload the file
    aws_config = config['aws']
    s3 = getBotoResource(aws_config)
    table = aws_config['table']
    bucket = s3.Bucket(aws_config['bucket'])
    basename = os.path.basename(filename)
    aws_name = f'{table}/{basename.replace("_","/")}'

    try:
        response = bucket.upload_file(filename, aws_name)
        print(f'awsUpload {basename} as {aws_name}')

    except Exception as e:
        print(f'Aws connector: {e}')
        return False    
    return True

def getBotoResource(aws_config):

    return boto3.resource( 's3',
                            endpoint_url = aws_config['endpoint_url'],
                            aws_access_key_id = aws_config['key_id'],
                            aws_secret_access_key = aws_config['key'],
                            region_name = aws_config['region'] )

# TEST code 
if  __name__ == "__main__":

    config = read_config()
    if validate_config(config) == False:
        quit()

    awsExport(config, 'chuck.txt')
    #awsImport(config, filename)

    #aws_config = config['aws']

    #bucket_name = aws_config['bucket']
    #s3 = getBotoResource(aws_config)
    #if s3 == None:
    #    quit()

    #bucket = s3.Bucket(bucket_name)
    # endpoint_url 
    #print(bucket)
    
    #print(dir(bucket))
    #try:
    #    bucket.upload_file('test.txt','test9.txt')
    #except Exception as e:
    #    print(f"Exception uploading file: {e}")
    #try:
    #    bucket.download_file('test1.txt','test2.txt')
    #except Exception as e:
    #    print(f"Exception uploading file: {e}")