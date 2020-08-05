import io
import boto3

S3_BUCKET = "clevercounseldevelopment"

s3_client = boto3.client("s3")

def upload_object(data, key):
    """
    uploads file-like object

    expects:
    - data
    - key (full path of file to save in s3)
    """

    if not key:
        key = data

    with io.BytesIO(data) as file:
        response = s3_client.upload_fileobj(file, S3_BUCKET, key)
        return response

    return {"error": "Could not complete upload"}