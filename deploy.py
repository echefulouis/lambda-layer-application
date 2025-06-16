#!/usr/bin/env python3
import subprocess
import sys
import os
import json
import boto3
import time
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def build_frontend():
    """Build the React frontend"""
    print("Building React frontend...")

    frontend_dir = Path("frontend")

    # Install dependencies
    run_command("npm install", cwd=frontend_dir)

    # Build the React app with environment variables
    build_command = "GENERATE_SOURCEMAP=false ESLINT_NO_DEV_ERRORS=true CI=false npm run build"
    run_command(build_command, cwd=frontend_dir)

    print("Frontend build completed successfully!")

def deploy_infrastructure():
    """Deploy the CDK infrastructure"""
    print("Deploying CDK infrastructure...")

    # Install Python dependencies
    run_command("pip install -r requirements.txt")

    # Deploy CDK stack
    result = run_command("cdk deploy --require-approval never --outputs-file cdk-outputs.json")

    print("Infrastructure deployed successfully!")

    # Read the outputs
    with open("cdk-outputs.json", "r") as f:
        outputs = json.load(f)

    return outputs

def upload_frontend(outputs):
    """Upload the built React app to S3"""
    print("Uploading frontend to S3...")

    # Get the frontend bucket name from CDK outputs
    stack_name = list(outputs.keys())[0]
    stack_outputs = outputs[stack_name]

    # Debug: Print available output keys
    print(f"Available output keys: {list(stack_outputs.keys())}")

    # Try different possible key names for backwards compatibility
    frontend_bucket = None
    api_url = None

    # Look for frontend bucket
    for key in ["FrontendBucket", "FrontendBucketOutput"]:
        if key in stack_outputs:
            frontend_bucket = stack_outputs[key]
            break

    # Look for API URL
    for key in ["ApiUrl", "ApiUrlOutput"]:
        if key in stack_outputs:
            api_url = stack_outputs[key]
            break

    # Look for CloudFront Distribution ID
    distribution_id = None
    for key in ["CloudFrontDistributionId", "CloudFrontDistributionIdOutput"]:
        if key in stack_outputs:
            distribution_id = stack_outputs[key]
            break

    if not frontend_bucket:
        raise Exception(f"Frontend bucket not found in outputs. Available keys: {list(stack_outputs.keys())}")

    if not api_url:
        raise Exception(f"API URL not found in outputs. Available keys: {list(stack_outputs.keys())}")

    print(f"Using frontend bucket: {frontend_bucket}")
    print(f"Using API URL: {api_url}")

    # Update the API URL in the built frontend
    build_dir = Path("frontend/build")

    # Find and update the JavaScript files with the actual API URL
    files_updated = 0
    for js_file in build_dir.glob("static/js/*.js"):
        with open(js_file, "r") as f:
            content = f.read()

        # Replace the placeholder API URL with the actual one
        old_content = content
        content = content.replace(
            "https://your-api-id.execute-api.your-region.amazonaws.com/prod",
            api_url
        )

        if content != old_content:
            files_updated += 1
            print(f"Updated API URL in: {js_file.name}")
            with open(js_file, "w") as f:
                f.write(content)

    print(f"Updated API URL in {files_updated} JavaScript files")

    # Also create a config file as backup method
    config_content = f"""window.APP_CONFIG = {{
  API_URL: "{api_url}"
}};"""

    config_path = build_dir / "config.js"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created config file: {config_path}")

    # Update index.html to include config.js
    index_path = build_dir / "index.html"
    if index_path.exists():
        with open(index_path, "r") as f:
            html_content = f.read()

        # Add config.js script before closing head tag
        if 'config.js' not in html_content:
            html_content = html_content.replace(
                '</head>',
                '  <script src="./config.js"></script>\n</head>'
            )
            with open(index_path, "w") as f:
                f.write(html_content)
            print("Added config.js to index.html")

    # Upload to S3
    s3_client = boto3.client('s3')

    def upload_file(local_file, s3_key):
        content_type = "text/html"
        if s3_key.endswith('.js'):
            content_type = "application/javascript"
        elif s3_key.endswith('.css'):
            content_type = "text/css"
        elif s3_key.endswith('.png'):
            content_type = "image/png"
        elif s3_key.endswith('.jpg') or s3_key.endswith('.jpeg'):
            content_type = "image/jpeg"
        elif s3_key.endswith('.ico'):
            content_type = "image/x-icon"
        elif s3_key.endswith('.json'):
            content_type = "application/json"

        s3_client.upload_file(
            str(local_file),
            frontend_bucket,
            s3_key,
            ExtraArgs={'ContentType': content_type}
        )

    # Upload all files from the build directory
    for file_path in build_dir.rglob("*"):
        if file_path.is_file():
            s3_key = str(file_path.relative_to(build_dir))
            upload_file(file_path, s3_key)

    print(f"Frontend uploaded to S3 bucket: {frontend_bucket}")

    # Create CloudFront invalidation to refresh cache
    if distribution_id:
        print(f"Creating CloudFront invalidation for distribution: {distribution_id}")
        try:
            cloudfront_client = boto3.client('cloudfront')

            invalidation_response = cloudfront_client.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': 1,
                        'Items': ['/*']  # Invalidate all files
                    },
                    'CallerReference': f'deploy-{int(time.time())}'
                }
            )

            invalidation_id = invalidation_response['Invalidation']['Id']
            print(f"✅ CloudFront invalidation created: {invalidation_id}")
            print("⏱️  Cache invalidation is in progress (may take 5-15 minutes)")

        except Exception as invalidation_error:
            print(f"⚠️  Warning: CloudFront invalidation failed: {str(invalidation_error)}")
            print("   Your deployment was successful, but cached files may take time to update")
    else:
        print("⚠️  CloudFront Distribution ID not found - skipping cache invalidation")

    return outputs

def main():
    """Main deployment function"""
    print("Starting Lambda Package Builder deployment...")

    try:
        # Build the React frontend
        build_frontend()

        # Deploy the CDK infrastructure
        outputs = deploy_infrastructure()

        # Upload the frontend to S3
        outputs = upload_frontend(outputs)

        # Print success information
        stack_name = list(outputs.keys())[0]
        stack_outputs = outputs[stack_name]

        # Get output values with flexible key names
        def get_output_value(possible_keys):
            for key in possible_keys:
                if key in stack_outputs:
                    return stack_outputs[key]
            return "Not found"

        frontend_url = get_output_value(["FrontendUrl", "FrontendUrlOutput"])
        cloudfront_url = get_output_value(["CloudFrontUrl", "CloudFrontUrlOutput"])
        custom_domain = get_output_value(["CustomDomain", "CustomDomainOutput"])
        distribution_id = get_output_value(["CloudFrontDistributionId", "CloudFrontDistributionIdOutput"])
        api_url = get_output_value(["ApiUrl", "ApiUrlOutput"])
        lambda_bucket = get_output_value(["LambdaPackagesBucket", "LambdaPackagesBucketOutput"])
        frontend_bucket = get_output_value(["FrontendBucket", "FrontendBucketOutput"])

        print("\n" + "="*70)
        print("🎉 DEPLOYMENT SUCCESSFUL! 🎉")
        print("="*70)
        print(f"🌐 Custom Domain:     {frontend_url}")
        if cloudfront_url != "Not found":
            print(f"☁️  CloudFront URL:    {cloudfront_url}")
        print(f"🔗 API URL:           {api_url}")
        print(f"📦 Lambda Bucket:     {lambda_bucket}")
        print(f"🗂️  Frontend Bucket:   {frontend_bucket}")

        print(f"\n🚀 Your Lambda Layer Builder is now live at:")
        print(f"   👉 {frontend_url}")

        if custom_domain != "Not found":
            print(f"\n📋 DNS Setup:")
            print(f"   ✅ Custom domain: {custom_domain}")
            print(f"   ✅ SSL certificate will be auto-validated")
            print(f"   ⏱️  DNS propagation may take 5-10 minutes")

        if distribution_id != "Not found":
            print(f"\n☁️  CloudFront:")
            print(f"   🆔 Distribution ID: {distribution_id}")
            print(f"   🔄 Cache invalidation initiated")
            print(f"   ⏱️  Cache refresh may take 5-15 minutes")

        print("="*70)

    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()