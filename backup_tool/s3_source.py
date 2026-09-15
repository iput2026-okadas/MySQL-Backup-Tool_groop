
import boto3
# https://dev.classmethod.jp/articles/try-boto3-stubs/
# for type hint in vscode


from backup_tool.mysql_source import MySQLSource
from backup_tool.config import AWSConfig


class S3Source(MySQLSource):

    def __init__(
            self,
            mysql_config,
            s3_config: AWSConfig,
            target_file,
        ):
        super().__init__(
            mysql_config,
        )
        self._s3_config = s3_config
        self._target_file = target_file

        self._parts = []
        self._single_buffer_size = 50 * 1024 * 1024
        self._part_num = 1
        
        try:
            self._s3 = boto3.Session(
                profile_name=self._s3_config.profile,
                region_name=self._s3_config.region, 
            ).client("s3")


            self._mpu = self._s3.create_multipart_upload(
                Key=self._target_file,
                Bucket=self._s3_config.bucket,
            )
            self._upload_id = self._mpu["UploadId"]

        except Exception as e:
            print(e)


    def _upload_part(
            self,
            body,
        ):
        try:
            res = self._s3.upload_part(
                Key=self._target_file,
                Bucket=self._s3_config.bucket,
                UploadId=self._upload_id,
                PartNumber=self._part_num,
                Body=body,
            )
            self._parts.append({"ETag": res["ETag"], "PartNumber": self._part_num})
            self._part_num += 1

            return None

        except Exception as e:
            print(e)

    def _complete_upload(
        self,
    ) -> None:
        try:
            self._s3.complete_multipart_upload(
                Key=self._target_file,
                Bucket=self._s3_config.bucket,
                UploadId=self._upload_id,
                MultipartUpload={'Parts': self._parts}
            )

        except Exception as e:
            print(e)

        finally:
            print(f"Upload of {self._target_file}  is completed")

    def _abort(
        self,
    ) -> None:
        try:
            self._s3.abort_multipart_upload(
                Key=self._target_file,
                Bucket=self._s3_config.bucket,
                UploadId=self._upload_id,
            )

        except Exception as e:
            print(e)