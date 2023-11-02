import os
import boto3
from botocore.config import Config
from urllib3.contrib.socks import SOCKSProxyManager

class S3Uploader:
    def __init__(self, settings) -> None:
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings["aws_access_key_id"],
            aws_secret_access_key=settings["aws_secret_access_key"],
            region_name=settings["region_name"],
            config=Config(s3={"addressing_style": "path"}),
        )
        self.client._endpoint.http_session._manager = SOCKSProxyManager(
            f'socks5h://{os.environ["ACTCAST_SOCKS_SERVER"]}'
        )

    def upload(self, filename, bucket, key):
        self.client.upload_file("./" + filename, bucket, key)
