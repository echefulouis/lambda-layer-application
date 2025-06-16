"""
Basic tests for Lambda functions to ensure they have correct structure
and can be imported without errors.
"""
import pytest
import json
from unittest.mock import Mock, patch


def test_package_creator_import():
    """Test that package_creator can be imported and has required function."""
    from lambda_functions import package_creator
    assert hasattr(package_creator, 'lambda_handler')
    assert callable(package_creator.lambda_handler)


def test_package_lister_import():
    """Test that package_lister can be imported and has required function."""
    from lambda_functions import package_lister
    assert hasattr(package_lister, 'lambda_handler')
    assert callable(package_lister.lambda_handler)


def test_download_url_generator_import():
    """Test that download_url_generator can be imported and has required function."""
    from lambda_functions import download_url_generator
    assert hasattr(download_url_generator, 'lambda_handler')
    assert callable(download_url_generator.lambda_handler)


@patch('lambda_functions.package_creator.s3_client')
def test_package_creator_invalid_input(mock_s3):
    """Test package creator handles invalid input gracefully."""
    from lambda_functions.package_creator import lambda_handler
    
    # Test with empty event
    event = {'body': '{}'}
    context = Mock()
    context.get_remaining_time_in_millis.return_value = 300000
    
    result = lambda_handler(event, context)
    
    # Should return a valid response structure
    assert 'statusCode' in result
    assert 'headers' in result
    assert 'body' in result
    assert 'Access-Control-Allow-Origin' in result['headers']


@patch('lambda_functions.package_lister.s3_client')
def test_package_lister_empty_bucket(mock_s3):
    """Test package lister handles empty bucket gracefully."""
    from lambda_functions.package_lister import lambda_handler
    
    # Mock empty bucket response
    mock_s3.list_objects_v2.return_value = {}
    
    event = {}
    context = Mock()
    
    result = lambda_handler(event, context)
    
    # Should return a valid response with empty packages list
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['success'] is True
    assert 'packages' in body
    assert body['count'] == 0


@patch('lambda_functions.download_url_generator.s3_client')
def test_download_url_generator_missing_key(mock_s3):
    """Test download URL generator handles missing S3 key."""
    from lambda_functions.download_url_generator import lambda_handler
    
    event = {
        'pathParameters': {'s3Key': 'nonexistent-key.zip'}
    }
    context = Mock()
    
    # Mock S3 exception
    mock_s3.generate_presigned_url.side_effect = Exception("Object not found")
    
    result = lambda_handler(event, context)
    
    # Should return error response
    assert result['statusCode'] == 500
    body = json.loads(result['body'])
    assert body['success'] is False
    assert 'error' in body


def test_lambda_function_environment_variables():
    """Test that Lambda functions handle missing environment variables."""
    import os
    
    # Temporarily remove BUCKET_NAME if it exists
    original_bucket = os.environ.get('BUCKET_NAME')
    if 'BUCKET_NAME' in os.environ:
        del os.environ['BUCKET_NAME']
    
    try:
        from lambda_functions import package_creator
        # Should not raise ImportError even without env vars
        assert hasattr(package_creator, 'lambda_handler')
    finally:
        # Restore original environment
        if original_bucket:
            os.environ['BUCKET_NAME'] = original_bucket


def test_package_creator_cleanup_function():
    """Test cleanup_installation function handles errors gracefully."""
    from lambda_functions.package_creator import cleanup_installation
    import tempfile
    import os
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = os.path.join(temp_dir, 'test_packages')
        os.makedirs(test_dir)
        
        # Create some test files
        with open(os.path.join(test_dir, 'test.pyc'), 'w') as f:
            f.write('test')
        
        # Should not raise exceptions
        cleanup_installation(test_dir)


def test_install_packages_functions_exist():
    """Test that the new install package functions exist."""
    from lambda_functions import package_creator
    
    assert hasattr(package_creator, 'install_packages_individually')
    assert hasattr(package_creator, 'install_packages_together')
    assert callable(package_creator.install_packages_individually)
    assert callable(package_creator.install_packages_together) 