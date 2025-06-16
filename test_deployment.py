#!/usr/bin/env python3
import json
import requests
import sys

def test_deployment():
    """Test if the deployed Lambda Layer Builder is working"""
    
    print("🔍 Testing Lambda Layer Builder deployment...")
    
    # Read CDK outputs to get API URL
    try:
        with open("cdk-outputs.json", "r") as f:
            outputs = json.load(f)
        
        stack_name = list(outputs.keys())[0]
        api_url = outputs[stack_name].get("ApiUrl") or outputs[stack_name].get("ApiUrlOutput")
        frontend_url = outputs[stack_name].get("FrontendUrl") or outputs[stack_name].get("FrontendUrlOutput")
        cloudfront_url = outputs[stack_name].get("CloudFrontUrl") or outputs[stack_name].get("CloudFrontUrlOutput")
        custom_domain = outputs[stack_name].get("CustomDomain") or outputs[stack_name].get("CustomDomainOutput")
        distribution_id = outputs[stack_name].get("CloudFrontDistributionId") or outputs[stack_name].get("CloudFrontDistributionIdOutput")
        
        if not api_url:
            print("❌ API URL not found in CDK outputs")
            return False
            
        print(f"📡 API URL: {api_url}")
        print(f"🌐 Custom Domain: {frontend_url}")
        if cloudfront_url:
            print(f"☁️  CloudFront URL: {cloudfront_url}")
        if custom_domain:
            print(f"🏷️  Domain Name: {custom_domain}")
        if distribution_id:
            print(f"🆔 Distribution ID: {distribution_id}")
        
    except FileNotFoundError:
        print("❌ cdk-outputs.json not found. Run deployment first.")
        return False
    except Exception as e:
        print(f"❌ Error reading CDK outputs: {e}")
        return False
    
    # Test API health
    try:
        print("\n🏥 Testing API health...")
        response = requests.get(f"{api_url}/packages", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ API is healthy! Found {data.get('count', 0)} layers")
            else:
                print(f"⚠️  API responded but with error: {data.get('error', 'Unknown')}")
        else:
            print(f"⚠️  API returned status code: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ API request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False
    
    # Test CORS
    try:
        print("\n🔐 Testing CORS configuration...")
        response = requests.options(f"{api_url}/packages")
        cors_headers = response.headers.get('Access-Control-Allow-Origin', '')
        
        if cors_headers == '*':
            print("✅ CORS is configured correctly")
        else:
            print(f"⚠️  CORS may be misconfigured: {cors_headers}")
            
    except Exception as e:
        print(f"⚠️  CORS test failed: {e}")
    
    print(f"\n🎉 Deployment test completed!")
    print(f"📋 Next steps:")
    print(f"   1. Open your browser to: {frontend_url}")
    if cloudfront_url and cloudfront_url != frontend_url:
        print(f"      (Backup URL: {cloudfront_url})")
    print(f"   2. Note: DNS propagation may take 5-10 minutes for custom domain")
    print(f"   3. Check browser console for any API connection errors")
    print(f"   4. Try creating a layer with some dependencies")
    
    return True

if __name__ == "__main__":
    success = test_deployment()
    sys.exit(0 if success else 1) 