from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
)
from constructs import Construct

class EcsApixHandsOnStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

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

        db_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(5432)
        )

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
            ]
        )
