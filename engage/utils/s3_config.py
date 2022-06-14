import boto3
from getenv import env
import logging
from typing import Optional


class AwsS3Config:
    """
    Helper class to configure a feature with separate S3 auth creds, given a prefix.
    """

    def __init__(self, aEnvVarPrefix=''):
        thePrefix = aEnvVarPrefix + (
            '_' if aEnvVarPrefix and len(aEnvVarPrefix) > 1 and not aEnvVarPrefix.endswith('_') else ''
        )
        self.aws_session: Optional[boto3.Session] = None
        self.aws_client = None
        self.AWS_S3_ACCESS_KEY_ID = env(f"{thePrefix}AWS_S3_ACCESS_KEY_ID", "NOT_SET")
        self.AWS_S3_SECRET_KEY = env(f"{thePrefix}AWS_S3_SECRET_KEY", "NOT_SET")
        self.AWS_S3_ENDPOINT_URL = env(f"{thePrefix}AWS_S3_ENDPOINT_URL", "")
        self.AWS_S3_REGION = env(f"{thePrefix}AWS_S3_REGION", "us-east-1")
        self.AWS_S3_BUCKET = env(f"{thePrefix}AWS_S3_BUCKET", "")
        self.FILEPATH = env(f"{thePrefix}FILEPATH", "")
    #enddef init

    def is_defined(self):
        return self.AWS_S3_BUCKET and len(self.AWS_S3_BUCKET) > 1 and \
               self.AWS_S3_ACCESS_KEY_ID and self.AWS_S3_ACCESS_KEY_ID != 'NOT_SET'
    #enddef is_defined()

    def get_session(self):
        if self.aws_session is None:
            self.aws_session = boto3.session.Session(
                aws_access_key_id=self.AWS_S3_ACCESS_KEY_ID,
                aws_secret_access_key=self.AWS_S3_SECRET_KEY,
            )
        #endif
        return self.aws_session
    #enddef get_session()

    def get_client(self):
        if self.aws_client is None:
            if self.AWS_S3_ENDPOINT_URL:
                self.aws_client = self.get_session().client('s3',
                        endpoint_url=self.AWS_S3_ENDPOINT_URL,
                        region_name=self.AWS_S3_REGION,
                )
            else:
                self.aws_client = self.get_session().client('s3',
                        region_name=self.AWS_S3_REGION,
                )
            #endif
        #endif
        return self.aws_client
    #enddef get_client()

    def get_obj(self, aObjPath: str = ''):
        logger = logging.getLogger(__name__)
        theObjKey = aObjPath if aObjPath and len(aObjPath) > 1 else self.FILEPATH
        theObj = self.get_client().get_object(Bucket=self.AWS_S3_BUCKET, Key=theObjKey)
        logger.debug("served user guide", extra={
            'bucket': self.AWS_S3_BUCKET,
            'filepath': theObjKey,
        })
        return theObj
    #enddef get_obj()

#endclass AwsS3Config
