from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_logs as logs,
)
from constructs import Construct
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import aws_cloudtrail as aws_cloudtrail
from aws_cdk import aws_events as events
from aws_cdk import aws_s3 as aws_s3
from aws_cdk import aws_events_targets as events_targets

class EventBridgeLambdaStepfunctionStack(Stack):


    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "EventBridgeLambdaStepfunctionQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )


        hello_world_lambda = _lambda.Function(
            self,
            "HelloWorldHandler",
            function_name="hello_world",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("lambda"),
            handler="helloworld.lambda_handler"
        )

        definition = tasks.LambdaInvoke(self,
            "Invoke Lambda - HelloLambda",
            lambda_function=hello_world_lambda,
            result_path="$.Payload",
        ).add_retry(max_attempts=3).next(
            sfn.Succeed(self, "Success")
        )
                                        
        log_group = logs.LogGroup(self, "LogGroup",
            log_group_name="s3-connection-log-group",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )
        # Create the Step Function state machine
        stateMachine = sfn.StateMachine(self, "StateMachine",
            definition=definition,
            state_machine_name="s3-connection-state-machine",
            timeout=Duration.minutes(5),
            logs=sfn.LogOptions(
                destination=log_group,
                include_execution_data=True,
                level=sfn.LogLevel.ALL,
            ),
        )

        # # create a s3 bucket
        s3_log_bucket = aws_s3.Bucket(self, "S3Bucket",
            bucket_name="sran-sfn-tutorial",
            removal_policy=RemovalPolicy.DESTROY,
            event_bridge_enabled=True,
            auto_delete_objects=True,
        )
        # # create cloudtrail trail log group

        log_group = logs.LogGroup(
            self,
            "loggroup",
            log_group_name="loggroup-s3trail",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )
        # # create a cloudTrail event
        cloudtrail_trail = aws_cloudtrail.Trail(
            self,
            "cloudtrailtrailforbucketcreation",
            bucket=s3_log_bucket,
            is_multi_region_trail=True,
            include_global_service_events=True,  # Include global service events
            send_to_cloud_watch_logs=True,
            enable_file_validation=True,
            trail_name="CustomCloudTrail",
            cloud_watch_logs_retention=logs.RetentionDays.ONE_DAY,
            cloud_watch_log_group=log_group,
        )

        # # create s3 bucket event
        bucket = aws_s3.Bucket(self, "Bucket",
            bucket_name="sran2-sfn-tutorial",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            event_bridge_enabled=True,
        )

       # # Adds an event selector to the bucket, when a file is uploaded to the bucket the rule will be triggered
        cloudtrail_trail.add_s3_event_selector(
            include_management_events=True,
            s3_selector=[aws_cloudtrail.S3EventSelector(bucket=bucket, object_prefix="")],
            exclude_management_event_sources=[
                aws_cloudtrail.ManagementEventSources.KMS,
                aws_cloudtrail.ManagementEventSources.RDS_DATA_API,
                ],
            read_write_type=aws_cloudtrail.ReadWriteType.ALL,
        )

        # Add an event selector for all S3 buckets
    # Add an event selector for all S3 buckets
        # cloudtrail_trail.add_event_selector(
        #     event_selector=aws_cloudtrail.S3EventSelector(
        #         data_resource_type=aws_cloudtrail.DataResourceType.S3_OBJECT,
        #         data_resource_values=[f"arn:aws:s3:::{bucket.bucket_name}/*"],
        #         include_management_events=True
        #     )
        # )

        # create a event to trigger the state machine when a file is uploaded to s3
        event_rule = events.Rule(self, "EventsRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["AWS API Call via CloudTrail"],
                detail={
                    "eventSource": ["s3.amazonaws.com"],
                    "eventName": ["PutObject"],
                    "requestParameters": {
                        "bucketName": [bucket.bucket_name]
                    }
                }
            )
        )
        target = events_targets
        event_rule.add_target(target.SfnStateMachine(stateMachine))