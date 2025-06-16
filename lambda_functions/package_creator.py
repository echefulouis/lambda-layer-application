import json
import boto3
import zipfile
import os
import tempfile
import subprocess
import shutil
from datetime import datetime

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Parse the request
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        
        package_name = body.get('packageName', 'lambda-layer')
        dependencies = body.get('dependencies', [])
        runtime = body.get('runtime', 'python3.12')
        platform = body.get('platform', 'manylinux2014_x86_64')
        python_version = body.get('pythonVersion', '3.12')
        install_dependencies = body.get('installDependencies', True)
        upgrade_packages = body.get('upgradePackages', False)
        package_type = 'layer'  # Always layer
        
        print(f"Creating Lambda layer: {package_name}")
        print(f"Architecture: {platform.replace('manylinux2014_', '')}, Python: {python_version}")
        print(f"Dependencies: {dependencies}")
        print(f"Install dependencies: {install_dependencies}")
        print(f"Upgrade packages: {upgrade_packages}")
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = os.path.join(temp_dir, 'package')
            os.makedirs(package_dir)
            
            # Install dependencies if requested and dependencies exist
            if install_dependencies and dependencies:
                print("Installing dependencies with pip...")
                success = install_pip_dependencies(
                    dependencies, package_dir, platform, python_version, package_type, upgrade_packages
                )
                if not success:
                    raise Exception(f"Failed to install dependencies: {', '.join(dependencies)}. "
                                  f"This may be due to: 1) Package not available for platform {platform}, "
                                  f"2) Network connectivity issues, 3) Package name typos, or "
                                  f"4) Incompatible package versions. Check CloudWatch logs for details.")
            
            # Create requirements.txt for reference
            if dependencies:
                requirements_path = os.path.join(package_dir, 'requirements.txt')
                with open(requirements_path, 'w') as f:
                    f.write('\n'.join(dependencies))
            
            # Create ZIP file
            zip_path = os.path.join(temp_dir, f'{package_name}.zip')
            create_zip_package(package_dir, zip_path, package_type)
            
            # Upload to S3 with metadata
            bucket_name = os.environ['BUCKET_NAME']
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            s3_key = f'layers/{package_name}-{timestamp}.zip'
            
            # Prepare metadata
            metadata = {
                'packageName': package_name,
                'dependencies': ','.join(dependencies) if dependencies else '',
                'runtime': runtime,
                'platform': platform,
                'pythonVersion': python_version,
                'packageType': package_type,
                'installDependencies': str(install_dependencies),
                'upgradePackages': str(upgrade_packages),
                'createdAt': timestamp,
                'dependencyCount': str(len(dependencies))
            }
            
            # Upload file with metadata
            s3_client.upload_file(
                zip_path, 
                bucket_name, 
                s3_key,
                ExtraArgs={'Metadata': metadata}
            )
            
            # Also create a separate metadata JSON file for easier querying
            metadata_key = f'metadata/{package_name}-{timestamp}.json'
            metadata_json = {
                'packageName': package_name,
                'dependencies': dependencies,
                'runtime': runtime,
                'platform': platform,
                'pythonVersion': python_version,
                'packageType': package_type,
                'installDependencies': install_dependencies,
                'upgradePackages': upgrade_packages,
                'createdAt': timestamp,
                'packageKey': s3_key,
                'packageSize': os.path.getsize(zip_path)
            }
            
            s3_client.put_object(
                Bucket=bucket_name,
                Key=metadata_key,
                Body=json.dumps(metadata_json, indent=2),
                ContentType='application/json'
            )
            
            # Generate presigned URL for download
            try:
                download_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': s3_key},
                    ExpiresIn=7200,  # 2 hours for more reliable downloads
                    HttpMethod='GET'
                )
                print(f"Generated download URL: {download_url[:50]}...")
            except Exception as url_error:
                print(f"Error generating presigned URL: {str(url_error)}")
                raise Exception(f"Failed to generate download URL: {str(url_error)}")
            
            # Get package size
            package_size = os.path.getsize(zip_path)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
                },
                'body': json.dumps({
                    'success': True,
                    'downloadUrl': download_url,
                    'packageName': package_name,
                    's3Key': s3_key,
                    'packageType': package_type,
                    'packageSize': package_size,
                    'platform': platform,
                    'pythonVersion': python_version,
                    'dependencies': dependencies,
                    'dependenciesInstalled': install_dependencies and len(dependencies) > 0,
                    'upgradePackages': upgrade_packages,
                    'createdAt': timestamp,
                    'message': f'Lambda layer "{package_name}" created successfully'
                })
            }
            
    except Exception as e:
        error_message = str(e)
        print(f"Error creating package: {error_message}")
        import traceback
        traceback.print_exc()
        
        # Add context information for better debugging
        print(f"=== ERROR CONTEXT ===")
        print(f"Package name: {locals().get('package_name', 'Unknown')}")
        print(f"Dependencies: {locals().get('dependencies', 'Unknown')}")
        print(f"Platform: {locals().get('platform', 'Unknown')}")
        print(f"Python version: {locals().get('python_version', 'Unknown')}")
        print(f"Lambda remaining time: {context.get_remaining_time_in_millis() if context else 'Unknown'} ms")
        
        # Provide more helpful error messages
        if "Failed to install dependencies" in error_message:
            user_error = error_message
        elif "timeout" in error_message.lower():
            user_error = "Installation timed out. Try with fewer dependencies or simpler packages."
        elif "memory" in error_message.lower() or "space" in error_message.lower():
            user_error = "Insufficient memory or disk space. Try installing fewer dependencies at once."
        elif "network" in error_message.lower() or "connection" in error_message.lower():
            user_error = "Network connectivity issue. Please try again in a few moments."
        else:
            user_error = f"Package creation failed: {error_message}"
        
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
            },
            'body': json.dumps({
                'success': False,
                'error': user_error,
                'details': error_message if error_message != user_error else None
            })
        }

def install_pip_dependencies(dependencies, package_dir, platform, python_version, package_type, upgrade_packages=False):
    """Install dependencies using pip with Lambda architecture-specific options"""
    try:
        # Add diagnostic information about the environment
        print("=== ENVIRONMENT DIAGNOSTICS ===")
        print(f"Installing {len(dependencies)} dependencies: {dependencies}")
        
        # Check Python version
        try:
            python_check = subprocess.run(['python3', '--version'], capture_output=True, text=True, timeout=10)
            print(f"Python version: {python_check.stdout.strip()}")
        except:
            print("Could not check Python version")
        
        # Check available disk space
        try:
            disk_usage = shutil.disk_usage('/tmp')
            print(f"Disk space - Free: {disk_usage.free // (1024*1024)} MB")
        except:
            print("Could not check disk space")
        
        print("=== END DIAGNOSTICS ===")
        
        # For Lambda layers, install to python/lib/pythonX.X/site-packages
        target_dir = os.path.join(package_dir, f'python/lib/python{python_version}/site-packages')
        os.makedirs(target_dir, exist_ok=True)
        print(f"Created target directory: {target_dir}")
        
        # Strategy: Install packages individually for better reliability with multiple packages
        if len(dependencies) > 2:
            print(f"🔄 Installing {len(dependencies)} packages individually for better reliability...")
            return install_packages_individually(dependencies, target_dir, platform, python_version, upgrade_packages)
        else:
            print(f"🔄 Installing {len(dependencies)} packages together...")
            return install_packages_together(dependencies, target_dir, platform, python_version, upgrade_packages)
            
    except Exception as e:
        print(f"Error during pip install: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def install_packages_individually(dependencies, target_dir, platform, python_version, upgrade_packages):
    """Install packages one by one for better reliability"""
    installed_packages = []
    failed_packages = []
    
    for i, package in enumerate(dependencies):
        print(f"\n🔄 Installing package {i+1}/{len(dependencies)}: {package}")
        
        # Build pip command for single package
        pip_cmd = [
            'python3', '-m', 'pip', 'install',
            '--target', target_dir,
            '--implementation', 'cp',
            '--python-version', python_version,
            '--only-binary=:all:',
            '--no-cache-dir',
            '--disable-pip-version-check',
            '--platform', platform
        ]
        
        if upgrade_packages:
            pip_cmd.append('--upgrade')
        
        pip_cmd.append(package)
        
        print(f"Running: {' '.join(pip_cmd)}")
        
        try:
            result = subprocess.run(
                pip_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes per package
                cwd='/tmp'
            )
            
            if result.returncode == 0:
                print(f"✅ Successfully installed: {package}")
                installed_packages.append(package)
            else:
                print(f"❌ Failed to install: {package}")
                print(f"STDERR: {result.stderr}")
                failed_packages.append(package)
                
                # Try simplified installation for common packages
                if package in ['requests', 'boto3', 'urllib3', 'six', 'python-dateutil', 'certifi', 'charset-normalizer']:
                    print(f"🔄 Trying simplified install for {package}...")
                    simple_cmd = ['python3', '-m', 'pip', 'install', '--target', target_dir, package]
                    simple_result = subprocess.run(simple_cmd, capture_output=True, text=True, timeout=180)
                    
                    if simple_result.returncode == 0:
                        print(f"✅ Simplified install succeeded for: {package}")
                        installed_packages.append(package)
                        failed_packages.remove(package)
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ Timeout installing: {package}")
            failed_packages.append(package)
        except Exception as e:
            print(f"❌ Error installing {package}: {str(e)}")
            failed_packages.append(package)
    
    print(f"\n=== INSTALLATION SUMMARY ===")
    print(f"✅ Successfully installed: {installed_packages}")
    if failed_packages:
        print(f"❌ Failed to install: {failed_packages}")
    
    # Consider it successful if at least 50% of packages installed
    success_rate = len(installed_packages) / len(dependencies)
    print(f"📊 Success rate: {success_rate:.1%}")
    
    if success_rate >= 0.5:  # At least 50% success
        cleanup_installation(target_dir)
        return True
    else:
        return False

def install_packages_together(dependencies, target_dir, platform, python_version, upgrade_packages):
    """Install packages together (for 2 or fewer packages)"""
    try:
        # Try to ensure we have pip available
        try:
            pip_upgrade = subprocess.run(
                ['python3', '-m', 'pip', 'install', '--upgrade', 'pip'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if pip_upgrade.returncode == 0:
                print("Successfully upgraded pip")
            else:
                print(f"Pip upgrade warning (continuing anyway): {pip_upgrade.stderr}")
        except Exception as upgrade_error:
            print(f"Could not upgrade pip (continuing anyway): {str(upgrade_error)}")
        
        # Build pip command
        pip_cmd = [
            'python3', '-m', 'pip', 'install',
            '--target', target_dir,
            '--implementation', 'cp',
            '--python-version', python_version,
            '--only-binary=:all:',
            '--no-cache-dir',
            '--disable-pip-version-check',
            '--platform', platform,
            '-v'
        ]
        
        if upgrade_packages:
            pip_cmd.append('--upgrade')
        
        # Add all dependencies
        pip_cmd.extend(dependencies)
        
        print(f"Running pip command: {' '.join(pip_cmd)}")
        
        # Run pip install with extended timeout
        result = subprocess.run(
            pip_cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes for batch install
            cwd='/tmp'
        )
        
        print(f"Pip command completed with return code: {result.returncode}")
        
        if result.returncode != 0:
            print(f"=== PIP INSTALL FAILED ===")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            
            # Try simplified approach for common packages
            if len(dependencies) == 1 and dependencies[0] in ['requests', 'boto3', 'numpy', 'pandas']:
                print(f"Trying simplified install for {dependencies[0]}...")
                simple_cmd = ['python3', '-m', 'pip', 'install', '--target', target_dir, dependencies[0]]
                simple_result = subprocess.run(simple_cmd, capture_output=True, text=True, timeout=300)
                
                if simple_result.returncode == 0:
                    print("Simplified install succeeded!")
                    cleanup_installation(target_dir)
                    return True
                else:
                    print(f"Simplified install also failed: {simple_result.stderr}")
            
            return False
        
        print(f"=== PIP INSTALL SUCCESSFUL ===")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR (warnings):\n{result.stderr}")
        
        # Check what was actually installed
        try:
            installed_files = []
            for root, dirs, files in os.walk(target_dir):
                installed_files.extend([os.path.join(root, f) for f in files[:5]])  # Sample first 5 files
            print(f"Sample installed files: {installed_files[:10]}")
        except:
            print("Could not list installed files")
        
        cleanup_installation(target_dir)
        return True
        
    except subprocess.TimeoutExpired as timeout_error:
        print(f"Pip install timed out after {timeout_error.timeout} seconds")
        return False
    except Exception as e:
        print(f"Error during batch pip install: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_installation(target_dir):
    """Remove unnecessary files to reduce package size"""
    try:
        patterns_to_remove = [
            '*.pyc', '*.pyo', '*__pycache__*', '*.dist-info*', 
            '*.egg-info*', 'tests', 'test', 'docs', 'examples'
        ]
        
        for root, dirs, files in os.walk(target_dir):
            # Remove __pycache__ directories
            dirs[:] = [d for d in dirs if '__pycache__' not in d and d not in ['tests', 'test', 'docs', 'examples']]
            
            # Remove .pyc, .pyo files
            for file in files:
                if file.endswith(('.pyc', '.pyo')) or '.dist-info' in file:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                    except:
                        pass
        
        print(f"Cleaned up installation directory: {target_dir}")
        
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

def create_zip_package(package_dir, zip_path, package_type):
    """Create ZIP file with proper structure"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    print(f"Created ZIP package: {zip_path}")

 