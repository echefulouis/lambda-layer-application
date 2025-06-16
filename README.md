# Lambda Layer Builder

[![CI - Build and Test](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/workflows/CI%20-%20Build%20and%20Test/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/actions)
[![CD - Deploy to AWS](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/workflows/CD%20-%20Deploy%20to%20AWS/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/actions)

A modern web application built with AWS CDK, React, and AWS services that helps developers create, customize, and download AWS Lambda Layers with platform-specific dependencies. The application provides an intuitive interface for building Lambda layers, managing dependencies, and generating ready-to-deploy ZIP files with automatic CI/CD deployment.

## Architecture

### Frontend
- **React**: Modern, responsive web interface
- **Monaco Editor**: Advanced code editor with syntax highlighting
- **S3 + CloudFront**: Static website hosting with global CDN

### Backend
- **API Gateway**: RESTful API endpoints
- **AWS Lambda**: Serverless compute for package processing
- **S3**: Storage for generated Lambda packages
- **IAM**: Fine-grained security policies

## Features

- 🚀 **Lambda Layer Builder**: Specialized tool for creating AWS Lambda Layers with platform-specific dependencies
- 🔍 **Smart Search**: Search through layers by name or dependencies with real-time filtering
- 📦 **Dependency Tracking**: Complete visibility of installed packages with version information
- 🏗️ **Platform Support**: x86_64 and ARM64 architecture support for optimal Lambda performance
- ⚡ **Optimized Installation**: Individual package installation for reliability with multiple dependencies
- 🌐 **Custom Domain**: Optional custom domain support with automatic SSL certificates
- ⬇️ **Instant Downloads**: Generate and download Lambda layers immediately with presigned URLs
- 📊 **Layer History**: View, search, and re-download previously created layers
- 🎨 **Modern UI**: Beautiful, responsive design with excellent UX and real-time feedback
- ☁️ **Serverless**: Fully serverless architecture with auto-scaling and CloudFront CDN
- 🔄 **Auto Cache Invalidation**: Automatic CloudFront cache invalidation on deployment

## Prerequisites

- **AWS CLI**: Configured with appropriate permissions
- **AWS CDK**: Version 2.x installed globally (`npm install -g aws-cdk`)
- **Node.js**: Version 16.x or higher
- **Python**: Version 3.8 or higher
- **Git**: For cloning the repository
- **Route 53 Hosted Zone**: (Optional) For custom domain setup

## Configuration

### 1. AWS Account Setup

Set your AWS account and region (optional - defaults to account 992382701391 and us-east-1):

```bash
export CDK_DEFAULT_ACCOUNT=your-account-id
export CDK_DEFAULT_REGION=your-preferred-region
```

### 2. Custom Domain Setup (Optional)

If you want to use a custom domain, update the domain configuration in `lambda_layer/lambda_layer_stack.py`:

```python
# Update these lines around line 25
domain_name = "your-domain.com"  # Replace with your domain
subdomain = "lambda-builder"     # Or your preferred subdomain
```

**Requirements for custom domain:**
- You must own a domain with a Route 53 hosted zone
- The hosted zone must be in the same AWS account you're deploying to

If you don't have a custom domain, the app will be available via CloudFront URL.

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd lambda_layer
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure (Optional)

```bash
# Set your AWS account/region if different from defaults
export CDK_DEFAULT_ACCOUNT=your-account-id
export CDK_DEFAULT_REGION=your-region

# Edit domain settings in lambda_layer/lambda_layer_stack.py if using custom domain
```

### 3. Deploy

```bash
python deploy.py
```

## CI/CD Pipeline

This project includes a complete CI/CD pipeline using GitHub Actions that automatically builds, tests, and deploys your application.

### 🚀 **Pipeline Features**

- **Continuous Integration**: Runs on pull requests and develop branch
  - Python code linting (flake8, black, isort)
  - Frontend linting (ESLint)
  - Unit tests with pytest
  - Security scanning (Bandit, npm audit)
  - CDK CloudFormation validation

- **Continuous Deployment**: Runs on main branch pushes
  - Automated AWS deployment using your existing `deploy.py` script
  - Post-deployment verification tests
  - Artifact storage for deployment outputs

### 🔧 **Setting Up GitHub Secrets**

To enable automated deployment, add these secrets to your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add the following repository secrets:

```bash
# Required for production deployment
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
CDK_DEFAULT_ACCOUNT=your-aws-account-id

# Optional for staging deployment
AWS_ACCESS_KEY_ID_STAGING=your-staging-aws-access-key-id
AWS_SECRET_ACCESS_KEY_STAGING=your-staging-aws-secret-access-key
CDK_DEFAULT_ACCOUNT_STAGING=your-staging-aws-account-id
```

### 🔐 **AWS IAM Permissions**

Create an IAM user with these permissions for GitHub Actions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sts:AssumeRole",
        "cloudformation:*",
        "s3:*",
        "lambda:*",
        "apigateway:*",
        "iam:*",
        "route53:*",
        "acm:*",
        "cloudfront:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### 🌲 **Branch Strategy**

- **`main`**: Production deployment (automatic)
- **`develop`**: Staging deployment (automatic)
- **`feature/*`**: CI only (no deployment)
- **Pull Requests**: CI only (no deployment)

### 📋 **Workflow Files**

- **`.github/workflows/ci.yml`**: Runs tests and builds on PRs
- **`.github/workflows/deploy.yml`**: Deploys to AWS on main/develop

### 🛠️ **Local Development**

Install pre-commit hooks for local code quality:

```bash
pip install pre-commit
pre-commit install
```

The deployment script will:
- Install React dependencies
- Build the React application
- Deploy AWS infrastructure via CDK
- Upload the frontend to S3
- Configure API endpoints

### 3. Access Your Application

After deployment, you'll see output like:
```
DEPLOYMENT SUCCESSFUL!
Frontend URL: https://d1234567890.cloudfront.net
API URL: https://abcdef1234.execute-api.us-east-1.amazonaws.com/prod/
```

Visit the Frontend URL to start using your Lambda Package Builder!

## Manual Deployment (Alternative)

If you prefer manual control over the deployment process:

### 1. Build Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### 2. Deploy Infrastructure
```bash
cdk deploy --outputs-file cdk-outputs.json
```

### 3. Upload Frontend
```bash
# Replace BUCKET_NAME with the actual frontend bucket name from CDK outputs
aws s3 sync frontend/build/ s3://BUCKET_NAME --delete
```

**Note**: This project uses `npm install` instead of `npm ci` since we don't commit `package-lock.json` files. The CI/CD pipeline will automatically generate lock files as needed.

## Usage Guide

### Creating Lambda Layers

1. **Configure Layer Settings**:
   - **Layer Name**: Enter a descriptive name for your layer
   - **Python Version**: Select target Python runtime (3.9, 3.10, 3.11, 3.12)
   - **Architecture**: Choose x86_64 or arm64 based on your Lambda functions

2. **Add Dependencies**:
   - Enter Python package names (e.g., `requests`, `fastapi`, `pandas`)
   - Use the quick-add buttons for common packages
   - Choose whether to upgrade packages to latest versions

3. **Generate Layer**: Click "Create Layer" to build and download your ZIP file
   - **1-2 dependencies**: Fast batch installation
   - **3+ dependencies**: Individual installation for better reliability
   - **Timeout**: Automatically adjusts based on dependency count (1-15 minutes)

### Layer Contents

Each generated layer includes:
- `python/lib/python3.X/site-packages/`: Properly structured for Lambda layers
- `requirements.txt`: List of installed dependencies
- Platform-specific binaries optimized for AWS Lambda

### Managing Layers

- **Search Layers**: Real-time search by layer name or dependencies
- **View Dependencies**: See all installed packages with dependency tags
- **Platform Info**: View Python version and architecture for each layer
- **Download Again**: Re-download any layer from the history
- **Layer Metadata**: View creation date, size, and dependency count

### Search Functionality

- Type in the search box to filter layers instantly
- Search works on both layer names and dependency names
- Examples:
  - Search "fastapi" to find all layers containing FastAPI
  - Search "requests" to find layers with the requests library
  - Search by layer name to find specific builds

## Project Structure

```
lambda_layer/
├── frontend/                 # React frontend application
│   ├── public/              # Static assets
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   └── App.js          # Main application
│   └── package.json        # Frontend dependencies
├── lambda_functions/        # Lambda function source code
│   ├── package_creator.py   # Package creation logic
│   ├── package_lister.py    # Package listing logic
│   └── download_url_generator.py # Download URL generation
├── lambda_layer/           # CDK infrastructure code
│   └── lambda_layer_stack.py # Main CDK stack
├── deploy.py              # Automated deployment script
├── app.py                # CDK app entry point
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/packages` | Create a new Lambda layer with dependencies |
| `GET` | `/packages` | List all created layers (supports `?search=` parameter) |
| `GET` | `/packages/{s3Key}/download` | Generate presigned download URL for a layer |

### API Parameters

**POST /packages**
```json
{
  "packageName": "my-fastapi-layer",
  "dependencies": ["fastapi", "uvicorn", "pydantic"],
  "pythonVersion": "3.12",
  "platform": "manylinux2014_x86_64",
  "upgradePackages": false
}
```

**GET /packages?search=fastapi**
- Returns layers containing "fastapi" in name or dependencies
- Search is case-insensitive and matches partial strings

## Common Layer Examples

### Web Framework Layer
```bash
# Dependencies for FastAPI/Flask applications
fastapi uvicorn pydantic
```

### Data Processing Layer
```bash
# Dependencies for data analysis
pandas numpy scipy
```

### AWS SDK Layer
```bash
# Enhanced AWS SDK with additional utilities
boto3 botocore requests
```

### Machine Learning Layer
```bash
# Basic ML libraries (note: may be large)
scikit-learn joblib
```

## Configuration

### Environment Variables

The application uses these environment variables:

- `BUCKET_NAME`: S3 bucket for storing Lambda packages (set automatically)

### Customization

#### Frontend Styling
Modify `frontend/src/App.css` to customize the application appearance.

#### Quick-Add Dependencies
Add common packages to the quick-add buttons in `frontend/src/components/PackageForm.js`.

#### API Configuration
Update API endpoints and timeouts in `frontend/src/services/api.js`.

#### Domain Configuration
Change the custom domain settings in `lambda_layer/lambda_layer_stack.py`.

## Security

### IAM Permissions

The application creates minimal IAM roles with these permissions:
- S3: Read/Write access to package bucket only
- Lambda: Basic execution role
- API Gateway: Invoke Lambda functions

### CORS Configuration

API Gateway is configured with CORS to allow frontend access:
```python
allow_origins=apigateway.Cors.ALL_ORIGINS,
allow_methods=apigateway.Cors.ALL_METHODS,
allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
```

### S3 Security

- Frontend bucket: Public read access for website hosting
- Packages bucket: Private with presigned URLs for downloads

## Troubleshooting

### Common Issues

1. **CDK Deploy Fails**
   ```bash
   # Bootstrap CDK if first time
   cdk bootstrap

   # If using custom domain, ensure hosted zone exists
   aws route53 list-hosted-zones
   ```

2. **Custom Domain Issues**
   ```bash
   # Verify hosted zone exists for your domain
   aws route53 list-hosted-zones --query "HostedZones[?Name=='yourdomain.com.']"

   # Check certificate validation status
   aws acm list-certificates --region us-east-1
   ```

3. **Layer Creation Timeouts**
   - Reduce number of dependencies (try 1-2 at a time)
   - Use simpler packages (avoid large libraries like pandas/numpy together)
   - Check CloudWatch logs for detailed pip installation output

4. **Frontend Build Errors**
   ```bash
   # Clear node modules and reinstall
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

5. **API CORS Errors**
   - Check that API URL is correctly set in frontend
   - Verify CORS configuration in CDK stack
   - Clear browser cache and try again

6. **Layer Download Failures**
   - Check S3 bucket permissions
   - Verify presigned URL generation
   - Try using CloudFront URL as backup

### Debugging

#### View Lambda Logs
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/LambdaLayerStack"
aws logs tail "/aws/lambda/LambdaLayerStack-PackageCreatorLambda" --follow
```

#### Check S3 Buckets
```bash
aws s3 ls  # List all buckets
aws s3 ls s3://your-bucket-name  # List bucket contents
```

## Development

### Local Development

For frontend development:
```bash
cd frontend
npm install  # Install dependencies first time
npm start    # Start development server on localhost:3000
```

### Running Tests Locally

```bash
# Python tests
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Code quality checks
flake8 lambda_functions/ lambda_layer/
black --check lambda_functions/ lambda_layer/
cd frontend && npm run lint
```

### Testing Lambda Functions

Test Lambda functions locally:
```bash
cd lambda_functions
python -c "
import package_creator
event = {'body': '{\"packageName\": \"test\", \"dependencies\": [\"requests\"]}'}
print(package_creator.lambda_handler(event, None))
"
```

## Cost Optimization

The application is designed to be cost-effective:

- **Lambda**: Pay-per-request pricing, minimal cold starts
- **S3**: Standard storage class, lifecycle policies available
- **CloudFront**: Free tier eligible for low traffic
- **API Gateway**: Pay-per-request pricing

### Cost Estimates (Monthly)

For moderate usage (100 packages/month):
- Lambda: ~$1
- S3: ~$2
- CloudFront: ~$1
- API Gateway: ~$1
- **Total: ~$5/month**

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow React best practices for frontend components
- Use Python PEP 8 style for Lambda functions
- Add appropriate error handling and logging
- Update documentation for new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with detailed description
4. Include logs and error messages

## Roadmap

Completed ✅:
- [x] Lambda Layer Builder with platform-specific dependencies
- [x] Search and filter layers by name/dependencies
- [x] Custom domain support with automatic SSL
- [x] Individual package installation for reliability
- [x] CloudFront cache invalidation on deployment
- [x] Enhanced error handling and timeout management

Future enhancements planned:
- [ ] Layer deletion functionality (clear layers)
- [ ] Support for Node.js Lambda layers
- [ ] Layer size optimization and compression
- [ ] Integration with AWS SAM CLI
- [ ] Multi-region deployment support
- [ ] Layer versioning and tagging
- [ ] Dependency vulnerability scanning
- [ ] Layer sharing and marketplace
- [ ] Docker-based builds for complex dependencies
