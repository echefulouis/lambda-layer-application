import aws_cdk as core
import aws_cdk.assertions as assertions

from lambda_layer.lambda_layer_stack import LambdaLayerStack

# example tests. To run these tests, uncomment this file along with the example
# resource in lambda_layer/lambda_layer_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = LambdaLayerStack(app, "lambda-layer")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
