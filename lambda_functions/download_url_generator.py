import json
import boto3
import os
from urllib.parse import unquote

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Get the S3 key from the path parameters
        s3_key = event.get('pathParameters', {}).get('s3Key')
        
        if not s3_key:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'S3 key is required'
                })
            }
        
        # URL decode the key
        s3_key = unquote(s3_key)
        bucket_name = os.environ['BUCKET_NAME']
        
        # Check if the object exists
        try:
            s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        except s3_client.exceptions.NoSuchKey:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Package not found'
                })
            }
        
        # Generate presigned URL for download
        try:
            download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': s3_key},
                ExpiresIn=7200,  # 2 hours for more reliable downloads
                HttpMethod='GET'
            )
            print(f"Generated download URL for {s3_key}: {download_url[:50]}...")
        except Exception as url_error:
            print(f"Error generating presigned URL for {s3_key}: {str(url_error)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'Failed to generate download URL: {str(url_error)}'
                })
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'downloadUrl': download_url,
                's3Key': s3_key
            })
        }
        
    except Exception as e:
        print(f"Error generating download URL: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        } 