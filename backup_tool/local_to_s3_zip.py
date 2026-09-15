

import boto3
from boto3.s3.transfer import TransferConfig

from backup_tool.config import AWSConfig, load_aws_config


def local_to_s3_zip(
    s3_config: AWSConfig,
    output_dir: str,
) -> None:
    config = TransferConfig(
        multipart_threshold= 1024 * 25,
        max_concurrency= 5,
        multipart_chunksize= 1024 * 25,
        use_threads= True,
    )

    s3 = boto3.Session(
        profile_name=s3_config.profile,
        region_name=s3_config.region, 
    ).client("s3")

    target = f"{output_dir}.zip"
    s3.upload_file(
        Filename= target,
        Bucket= s3_config.bucket,
        Key= target,
        Config= config,
    )

if __name__ == "__main__":
    config = load_aws_config(".mysql-backup/settings.env")
    name = input("name: ")

    local_to_s3_zip(config, name)