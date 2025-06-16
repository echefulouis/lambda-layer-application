import React from 'react';

const templates = {
  hello: {
    name: 'Hello World',
    description: 'Simple Lambda function that returns a greeting',
    code: `import json
from datetime import datetime

def lambda_handler(event, context):
    """
    Simple Hello World Lambda function
    """
    name = event.get('name', 'World')
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': f'Hello, {name}!',
            'timestamp': datetime.now().isoformat()
        })
    }`,
    dependencies: []
  },
  api: {
    name: 'API Gateway Handler',
    description: 'Process HTTP requests from API Gateway',
    code: `import json
import datetime

def lambda_handler(event, context):
    """
    API Gateway Lambda proxy integration handler
    """
    # Parse the HTTP method and path
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    query_params = event.get('queryStringParameters') or {}
    
    # Parse body for POST/PUT requests
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }
    
    # Route handling
    if http_method == 'GET' and path == '/':
        response_body = {
            'message': 'Welcome to the API',
            'timestamp': datetime.datetime.now().isoformat(),
            'path': path,
            'method': http_method
        }
    elif http_method == 'GET' and path == '/health':
        response_body = {
            'status': 'healthy',
            'timestamp': datetime.datetime.now().isoformat()
        }
    elif http_method == 'POST' and path == '/data':
        response_body = {
            'message': 'Data received',
            'received_data': body,
            'timestamp': datetime.datetime.now().isoformat()
        }
    else:
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Not found'})
        }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response_body)
    }`,
    dependencies: []
  },
  s3: {
    name: 'S3 Event Handler',
    description: 'Process S3 bucket events',
    code: `import json
import boto3
from urllib.parse import unquote_plus

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    S3 Event Handler - processes S3 bucket notifications
    """
    
    for record in event.get('Records', []):
        # Parse S3 event
        bucket_name = record['s3']['bucket']['name']
        object_key = unquote_plus(record['s3']['object']['key'])
        event_name = record['eventName']
        
        print(f"Processing {event_name} for {object_key} in bucket {bucket_name}")
        
        try:
            if event_name.startswith('ObjectCreated'):
                # Handle object creation
                handle_object_created(bucket_name, object_key)
            elif event_name.startswith('ObjectRemoved'):
                # Handle object deletion
                handle_object_removed(bucket_name, object_key)
            else:
                print(f"Unhandled event type: {event_name}")
                
        except Exception as e:
            print(f"Error processing {object_key}: {str(e)}")
            raise e
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed S3 events')
    }

def handle_object_created(bucket_name, object_key):
    """Handle S3 object creation events"""
    
    # Get object metadata
    response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
    file_size = response['ContentLength']
    content_type = response.get('ContentType', 'unknown')
    
    print(f"New object: {object_key}")
    print(f"Size: {file_size} bytes")
    print(f"Content Type: {content_type}")
    
    # Add your custom logic here
    # For example: resize images, extract metadata, trigger workflows, etc.
    
def handle_object_removed(bucket_name, object_key):
    """Handle S3 object deletion events"""
    
    print(f"Object deleted: {object_key}")
    
    # Add your custom logic here
    # For example: clean up related resources, update databases, etc.`,
    dependencies: ['boto3']
  },
  fastapi: {
    name: 'FastAPI + Mangum',
    description: 'FastAPI application with Mangum adapter for Lambda',
    code: `from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import json
from datetime import datetime
from typing import Dict, Any

# Create FastAPI app
app = FastAPI(
    title="Lambda FastAPI",
    description="FastAPI application running on AWS Lambda",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hello from FastAPI on Lambda!",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    """Get an item by ID"""
    if item_id < 1:
        raise HTTPException(status_code=400, detail="Item ID must be positive")
    
    return {
        "item_id": item_id,
        "query": q,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/items")
async def create_item(item: Dict[str, Any]):
    """Create a new item"""
    return {
        "message": "Item created successfully",
        "item": item,
        "created_at": datetime.now().isoformat()
    }

@app.get("/env")
async def get_environment():
    """Get environment information"""
    import os
    return {
        "aws_region": os.environ.get("AWS_REGION", "unknown"),
        "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
        "runtime": os.environ.get("AWS_EXECUTION_ENV", "unknown")
    }

# Mangum handler for AWS Lambda
lambda_handler = Mangum(app, lifespan="off")`,
    dependencies: ['fastapi', 'mangum']
  },
  dataapi: {
    name: 'Data Processing API',
    description: 'FastAPI with Pandas for data processing',
    code: `from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import pandas as pd
import json
import io
from typing import Dict, List, Any
from datetime import datetime

app = FastAPI(
    title="Data Processing API",
    description="FastAPI application for data processing with Pandas",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Data Processing API",
        "endpoints": [
            "/process-csv",
            "/analyze-data",
            "/health"
        ]
    }

@app.post("/process-csv")
async def process_csv(file: UploadFile = File(...)):
    """Process uploaded CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    try:
        # Read CSV data
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Basic analysis
        analysis = {
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_types": df.dtypes.astype(str).to_dict(),
            "summary_stats": df.describe().to_dict() if len(df.select_dtypes(include='number').columns) > 0 else {},
            "missing_values": df.isnull().sum().to_dict(),
            "processed_at": datetime.now().isoformat()
        }
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/analyze-data")
async def analyze_data(data: Dict[str, Any]):
    """Analyze JSON data using Pandas"""
    try:
        # Convert to DataFrame
        if "records" in data:
            df = pd.DataFrame(data["records"])
        else:
            df = pd.DataFrame([data])
        
        # Perform analysis
        numeric_columns = df.select_dtypes(include='number').columns.tolist()
        
        analysis = {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "numeric_columns": numeric_columns,
            "data_types": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict()
        }
        
        if numeric_columns:
            analysis["statistics"] = df[numeric_columns].describe().to_dict()
            analysis["correlations"] = df[numeric_columns].corr().to_dict()
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing data: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "pandas_version": pd.__version__,
        "timestamp": datetime.now().isoformat()
    }

# Lambda handler
lambda_handler = Mangum(app, lifespan="off")`,
    dependencies: ['fastapi', 'mangum', 'pandas']
  }
};

const CodeTemplates = ({ onTemplateLoad }) => {
  const handleLoadTemplate = (templateKey) => {
    const template = templates[templateKey];
    if (template) {
      onTemplateLoad(template.code, template.dependencies);
    }
  };

  return (
    <div className="form-group">
      <label>Code Templates</label>
      {Object.entries(templates).map(([key, template]) => (
        <div key={key} className="code-template">
          <div className="template-title">{template.name}</div>
          <div className="template-desc">{template.description}</div>
          <button 
            type="button" 
            className="btn btn-secondary" 
            onClick={() => handleLoadTemplate(key)}
          >
            <i className="fas fa-download"></i> Load
          </button>
        </div>
      ))}
    </div>
  );
};

export default CodeTemplates; 