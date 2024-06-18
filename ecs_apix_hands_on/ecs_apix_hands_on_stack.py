from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
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
