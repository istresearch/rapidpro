from datetime import timedelta
from django.utils.timezone import now
from shutil import rmtree
from tempfile import mkdtemp
from zipfile import ZipFile

import boto3
import dicttoxml
import json
import logging
import os

from .models import Msg, Label

logger = logging.getLogger(__name__)
dicttoxml.LOG.setLevel(logging.ERROR)

LABEL_PREFIX = os.getenv("CTO_LABEL_PREFIX", "CTO")
NAME_FORMAT = os.getenv("CTO_NAME_FORMAT", "MAD_{cto}_%Y-%m-%dT%H-%M-%S")
METADATA_DATE_FORMAT = os.getenv("CTO_METADATA_DATE_FORMAT", "%Y-%m-%dT%H:%M:%S")
INTERVAL_HOURS = int(os.getenv("CTO_INTERVAL_HOURS", "1"))
METADATA_UUID = os.getenv("CTO_METADATA_UUID", "00000000-0000-0000-0000-000000000000")

AWS_S3_ACCESS_KEY_ID = os.getenv("CTO_AWS_S3_ACCESS_KEY_ID", "CTO_AWS_S3_ACCESS_KEY_ID_NOT_SET")
AWS_S3_SECRET_ACCESS_KEY = os.getenv("CTO_AWS_S3_SECRET_ACCESS_KEY", "CTO_AWS_S3_SECRET_ACCESS_KEY_NOT_SET")
AWS_S3_ENDPOINT_URL = os.getenv("CTO_AWS_S3_ENDPOINT_URL", "s3.amazonaws.com")
AWS_S3_REGION = os.getenv("CTO_AWS_S3_REGION", "us-east-1")
AWS_S3_BUCKET = os.getenv("CTO_AWS_S3_BUCKET", "CTO_AWS_S3_BUCKET_NOT_SET")
AWS_S3_PATH = os.getenv("CTO_AWS_S3_PATH", "")

METADATA_FILE_TEMPLATE = '''Field1={first_msg}
Field2={last_msg}
Field3=
Field4=
Field5=
Field6=
Field7=
Field8=159
Field9=5
Field10=FILE
Field11=
Field12={cto_label}
Field13=
Field14=
Field15={uuid}'''

def export_cto_msgs():
    current_time = now()
    end_hour = current_time.hour - (current_time.hour % INTERVAL_HOURS)
    end_time = current_time.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=INTERVAL_HOURS)

    logger.info(json.dumps({"task": "export_cto_msgs", "start_time": str(start_time), "end_time": str(end_time)}))

    msgs = Msg.objects.filter(created_on__range=[start_time, end_time])
    cto_list = set()

    for msg in msgs:
        for label in msg.labels.all():
            if label.name.startswith(LABEL_PREFIX):
                cto_list.add(label)
    logger.info(json.dumps({"task": "export_cto_msgs", "total_message_count": msgs.count(), "cto_label_count": len(cto_list)}))

    for cto in cto_list:
        cto_msgs = msgs.filter(labels=cto.id).order_by('-created_on')
        if len(cto_msgs):
            cto_label = cto.name
            first_msg = cto_msgs.reverse()[0].created_on
            last_msg = cto_msgs[0].created_on
            xml_output = []
            for msg in cto_msgs:
                xml_output.append(msg.as_archive_json())
            filename = start_time.strftime(NAME_FORMAT.format(cto=cto_label))
            temp_dir = mkdtemp()
            working_dir = f"{temp_dir}/{filename}"
            os.mkdir(working_dir)
            with open(f"{working_dir}/{filename}.xml", "wb") as xml_file:
                xml_file.write(dicttoxml.dicttoxml(xml_output, custom_root='messages', attr_type=False))
            with open(f"{working_dir}/{filename}.txt", "w") as metadata_file:
                first_msg_label = first_msg.strftime(METADATA_DATE_FORMAT)
                last_msg_label = last_msg.strftime(METADATA_DATE_FORMAT)
                metadata_file.write(METADATA_FILE_TEMPLATE.format(first_msg=first_msg_label, last_msg=last_msg_label, cto_label=cto_label, uuid=METADATA_UUID))
            zipfile_path = f"{temp_dir}/{filename}.zip"
            with ZipFile(zipfile_path, "w") as zipfile:
                zipfile.write(f"{working_dir}/{filename}.xml", f"{filename}.xml")
                zipfile.write(f"{working_dir}/{filename}.txt", f"{filename}.txt")
                sess = boto3.session.Session(aws_access_key_id=AWS_S3_ACCESS_KEY_ID, aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY)
            client = sess.client('s3', endpoint_url=AWS_S3_ENDPOINT_URL, region_name=AWS_S3_REGION)
            object_path = f"{AWS_S3_PATH}/{filename}.zip" if AWS_S3_PATH else "{filename}.zip"
            response = client.upload_file(zipfile_path, AWS_S3_BUCKET, object_path)
            logger.info(json.dumps({"task": "export_cto_msgs", "cto": cto_label, "bucket": AWS_S3_BUCKET, "object_path": object_path}))
            rmtree(temp_dir)
