#!/usr/bin/env python3
import os

import aws_cdk as cdk

from lambda_layer.lambda_layer_stack import LambdaLayerStack


app = cdk.App()
LambdaLayerStack(app, "LambdaLayerStack",
    # Specify the AWS Account and Region for hosted zone lookup and domain configuration
    # You can override these with environment variables:
    # export CDK_DEFAULT_ACCOUNT=your-account-id
    # export CDK_DEFAULT_REGION=your-region
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT', '992382701391'),
        region=os.getenv('CDK_DEFAULT_REGION', 'us-east-1')
    ),
    )

app.synth()
