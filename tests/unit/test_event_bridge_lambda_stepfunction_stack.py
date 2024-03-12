import aws_cdk as core
import aws_cdk.assertions as assertions

from event_bridge_lambda_stepfunction.event_bridge_lambda_stepfunction_stack import EventBridgeLambdaStepfunctionStack

# example tests. To run these tests, uncomment this file along with the example
# resource in event_bridge_lambda_stepfunction/event_bridge_lambda_stepfunction_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EventBridgeLambdaStepfunctionStack(app, "event-bridge-lambda-stepfunction")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
