from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
    RemovalPolicy,
    Duration,
    CfnOutput,
)
from constructs import Construct
import os

class LambdaLayerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Domain configuration
        domain_name = "echefulouis.com"
        subdomain = "lambda-builder"
        full_domain = f"{subdomain}.{domain_name}"

        # Look up the existing hosted zone
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone",
            domain_name=domain_name
        )

        # Create SSL certificate for the subdomain
        certificate = acm.Certificate(
            self, "Certificate",
            domain_name=full_domain,
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

        # S3 bucket for storing lambda packages
        lambda_packages_bucket = s3.Bucket(
            self, "LambdaPackagesBucket",
            bucket_name=f"lambda-packages-{self.account}-{self.region}",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[s3.CorsRule(
                allowed_headers=["*"],
                allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.POST, s3.HttpMethods.PUT],
                allowed_origins=["*"],
                max_age=3000
            )]
        )

        # S3 bucket for hosting the web frontend
        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name=f"lambda-builder-frontend-{self.account}-{self.region}",
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # IAM role for Lambda functions
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "S3Access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListBucket",
                                "s3:HeadObject"
                            ],
                            resources=[
                                lambda_packages_bucket.bucket_arn,
                                f"{lambda_packages_bucket.bucket_arn}/*"
                            ]
                        )
                    ]
                )
            }
        )

        # Lambda function for creating lambda packages
        package_creator_lambda = _lambda.Function(
            self, "PackageCreatorLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="package_creator.lambda_handler",
            role=lambda_role,
            code=_lambda.Code.from_asset("lambda_functions"),
            timeout=Duration.minutes(15),  # Increased for dependency installation
            memory_size=1024,  # Increased for pip operations
            environment={
                'BUCKET_NAME': lambda_packages_bucket.bucket_name
            }
        )

        # Lambda function for listing available packages
        package_lister_lambda = _lambda.Function(
            self, "PackageListerLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="package_lister.lambda_handler",
            role=lambda_role,
            code=_lambda.Code.from_asset("lambda_functions"),
            timeout=Duration.minutes(1),
            environment={
                'BUCKET_NAME': lambda_packages_bucket.bucket_name
            }
        )

        # Lambda function for generating download URLs
        download_url_lambda = _lambda.Function(
            self, "DownloadUrlLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="download_url_generator.lambda_handler",
            role=lambda_role,
            code=_lambda.Code.from_asset("lambda_functions"),
            timeout=Duration.minutes(1),
            environment={
                'BUCKET_NAME': lambda_packages_bucket.bucket_name
            }
        )

        # API Gateway
        api = apigateway.RestApi(
            self, "LambdaBuilderApi",
            rest_api_name="Lambda Package Builder API",
            description="API for building and managing Lambda packages",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
            )
        )

        # API Gateway integrations
        create_package_integration = apigateway.LambdaIntegration(package_creator_lambda)
        list_packages_integration = apigateway.LambdaIntegration(package_lister_lambda)
        download_url_integration = apigateway.LambdaIntegration(download_url_lambda)

        # API endpoints
        packages_resource = api.root.add_resource("packages")
        packages_resource.add_method("POST", create_package_integration)
        packages_resource.add_method("GET", list_packages_integration)
        
        # Download endpoint: GET /packages/{s3Key}/download
        package_key_resource = packages_resource.add_resource("{s3Key}")
        download_resource = package_key_resource.add_resource("download")
        download_resource.add_method("GET", download_url_integration)

        # CloudFront distribution for the frontend
        distribution = cloudfront.Distribution(
            self, "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(frontend_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD
            ),
            domain_names=[full_domain],
            certificate=certificate,
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html"
                )
            ]
        )

        # Create Route 53 record pointing to CloudFront distribution
        route53.ARecord(
            self, "AliasRecord",
            zone=hosted_zone,
            record_name=subdomain,
            target=route53.RecordTarget.from_alias(targets.CloudFrontTarget(distribution))
        )

        # Outputs
        CfnOutput(
            self, "ApiUrlOutput",
            export_name="ApiUrl",
            value=api.url,
            description="API Gateway URL"
        )

        CfnOutput(
            self, "FrontendUrlOutput",
            export_name="FrontendUrl",
            value=f"https://{full_domain}",
            description="Frontend Custom Domain URL"
        )

        CfnOutput(
            self, "CloudFrontUrlOutput", 
            export_name="CloudFrontUrl",
            value=f"https://{distribution.domain_name}",
            description="Frontend CloudFront URL (backup)"
        )

        CfnOutput(
            self, "LambdaPackagesBucketOutput",
            export_name="LambdaPackagesBucket",
            value=lambda_packages_bucket.bucket_name,
            description="S3 bucket for lambda packages"
        )

        CfnOutput(
            self, "FrontendBucketOutput",
            export_name="FrontendBucket",
            value=frontend_bucket.bucket_name,
            description="S3 bucket for frontend hosting"
        )

        CfnOutput(
            self, "CustomDomainOutput",
            export_name="CustomDomain",
            value=full_domain,
            description="Custom domain name for the application"
        )

        CfnOutput(
            self, "CloudFrontDistributionIdOutput",
            export_name="CloudFrontDistributionId", 
            value=distribution.distribution_id,
            description="CloudFront Distribution ID for cache invalidation"
        )
