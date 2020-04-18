import boto3


def _get_s3_resource():
	AWSAccessKeyId="AKIAIGNAIE4VBZ2ZNLCA"
	AWSSecretKey="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"
	return boto3.resource(
		's3',
		aws_access_key_id=AWSAccessKeyId,
		aws_secret_access_key=AWSSecretKey
	)
	

def get_bucket():
	s3_resource = _get_s3_resource()

	return s3_resource.Bucket("surakhsa-storage")

