import json
import boto3
import os
from datetime import datetime

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        bucket_name = os.environ['BUCKET_NAME']
        
        # Get search query from query parameters
        search_query = ''
        if event.get('queryStringParameters'):
            search_query = event['queryStringParameters'].get('search', '').lower()
        
        # List metadata files first for better data
        metadata_response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='metadata/'
        )
        
        layers = []
        
        # Process metadata files if available
        if 'Contents' in metadata_response:
            for obj in metadata_response['Contents']:
                if obj['Key'].endswith('.json'):
                    try:
                        # Get metadata content
                        metadata_obj = s3_client.get_object(Bucket=bucket_name, Key=obj['Key'])
                        metadata_content = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                        
                        # Apply search filter if provided
                        if search_query:
                            # Search in package name and dependencies
                            package_name = metadata_content.get('packageName', '').lower()
                            dependencies = metadata_content.get('dependencies', [])
                            dependencies_str = ' '.join(dependencies).lower() if dependencies else ''
                            
                            if (search_query not in package_name and 
                                search_query not in dependencies_str):
                                continue
                        
                        layers.append({
                            'key': metadata_content.get('packageKey', ''),
                            'size': metadata_content.get('packageSize', 0),
                            'lastModified': obj['LastModified'].isoformat(),
                            'fileName': metadata_content.get('packageName', 'Unknown'),
                            'etag': obj['ETag'].strip('"'),
                            'dependencies': metadata_content.get('dependencies', []),
                            'runtime': metadata_content.get('runtime', ''),
                            'platform': metadata_content.get('platform', ''),
                            'pythonVersion': metadata_content.get('pythonVersion', ''),
                            'packageType': metadata_content.get('packageType', 'layer'),
                            'installDependencies': metadata_content.get('installDependencies', False),
                            'upgradePackages': metadata_content.get('upgradePackages', False),
                            'createdAt': metadata_content.get('createdAt', ''),
                            'dependencyCount': len(metadata_content.get('dependencies', []))
                        })
                    except Exception as e:
                        print(f"Error processing metadata file {obj['Key']}: {str(e)}")
                        continue
        
        # Fallback: List objects in the layers/ prefix for older packages without metadata
        if not layers:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='layers/'
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Skip directories
                    if obj['Key'].endswith('/'):
                        continue
                    
                    # Try to get object metadata
                    try:
                        head_response = s3_client.head_object(Bucket=bucket_name, Key=obj['Key'])
                        metadata = head_response.get('Metadata', {})
                        
                        # Parse dependencies from metadata
                        dependencies_str = metadata.get('dependencies', '')
                        dependencies = dependencies_str.split(',') if dependencies_str else []
                        dependencies = [dep.strip() for dep in dependencies if dep.strip()]
                        
                        # Apply search filter
                        if search_query:
                            package_name = metadata.get('packagename', obj['Key'].split('/')[-1]).lower()
                            dependencies_search = ' '.join(dependencies).lower()
                            
                            if (search_query not in package_name and 
                                search_query not in dependencies_search):
                                continue
                        
                        layers.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'lastModified': obj['LastModified'].isoformat(),
                            'fileName': obj['Key'].split('/')[-1],
                            'etag': obj['ETag'].strip('"'),
                            'dependencies': dependencies,
                            'runtime': metadata.get('runtime', ''),
                            'platform': metadata.get('platform', ''),
                            'pythonVersion': metadata.get('pythonversion', ''),
                            'packageType': metadata.get('packagetype', 'layer'),
                            'installDependencies': metadata.get('installdependencies', 'true').lower() == 'true',
                            'upgradePackages': metadata.get('upgradepackages', 'false').lower() == 'true',
                            'createdAt': metadata.get('createdat', ''),
                            'dependencyCount': len(dependencies)
                        })
                    except Exception as e:
                        print(f"Error getting metadata for {obj['Key']}: {str(e)}")
                        # Add basic info without metadata
                        if not search_query:  # Only include if no search filter
                            layers.append({
                                'key': obj['Key'],
                                'size': obj['Size'],
                                'lastModified': obj['LastModified'].isoformat(),
                                'fileName': obj['Key'].split('/')[-1],
                                'etag': obj['ETag'].strip('"'),
                                'dependencies': [],
                                'runtime': '',
                                'platform': '',
                                'pythonVersion': '',
                                'packageType': 'layer',
                                'installDependencies': False,
                                'upgradePackages': False,
                                'createdAt': '',
                                'dependencyCount': 0
                            })
        
        # Sort by last modified date (newest first)
        layers.sort(key=lambda x: x['lastModified'], reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'packages': layers,  # Keep 'packages' for frontend compatibility
                'count': len(layers),
                'searchQuery': search_query
            })
        }
        
    except Exception as e:
        print(f"Error listing layers: {str(e)}")
        import traceback
        traceback.print_exc()
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