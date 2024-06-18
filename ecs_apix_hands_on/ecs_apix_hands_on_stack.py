from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_secretsmanager as sm,
    aws_ecs_patterns as ecs_patterns,
)
from constructs import Construct


class EcsApixHandsOnStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        docker_tag = self.node.try_get_context("docker_tag")

        ecs_task_role = iam.Role(
            self,
            "EcsTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Grant access to multiple AWS services",
        )

        vpc = ec2.Vpc(
            self,
            "EcsApixVpc",
            max_azs=2,
        )

        db_sg = ec2.SecurityGroup(
            self,
            "EcsApixDbSg",
            vpc=vpc,
            allow_all_outbound=True,
        )

        db_sg.add_ingress_rule(peer=ec2.Peer.any_ipv4(), connection=ec2.Port.tcp(5432))

        database_cluster = rds.DatabaseCluster(
            self,
            "EcsApixDbCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_16_1,
            ),
            serverless_v2_max_capacity=16,
            serverless_v2_min_capacity=0.5,
            credentials=rds.Credentials.from_generated_secret("clusteradmin"),
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            ),
            writer=rds.ClusterInstance.serverless_v2("writer1"),
            security_groups=[
                db_sg,
            ],
            vpc=vpc,
        )

        cluster = ecs.Cluster(
            self,
            "ApixEcsCluster",
            vpc=vpc,
        )

        ecr_repository = ecr.Repository.from_repository_name(
            self,
            "ApixEcrRepo",
            "emilio-ghactions-demo",
        )

        ecr_image = ecs.ContainerImage.from_ecr_repository(
            ecr_repository,
            docker_tag,
        )

        secret = sm.Secret.from_secret_attributes(
            self,
            "ApixDbSecret",
            secret_complete_arn=database_cluster.secret.secret_arn,
        )

        fargate_cluster = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "ApixEcsService",
            cluster=cluster,
            memory_limit_mib=1024,
            cpu=512,
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecr_image,
                task_role=ecs_task_role,
                environment={
                    "DB_NAME": "postgres",
                    "DB_USERNAME": secret.secret_value_from_json(
                        "username"
                    ).to_string(),
                    "DB_PASSWORD": secret.secret_value_from_json(
                        "password"
                    ).to_string(),
                    "DB_HOST": secret.secret_value_from_json("host").to_string(),
                },
            ),
        )
