import boto3


class s3Wrapper:
    """
    Interact with aws s3 using boto3
    """

    def __init__(self, access_key_id: str, access_secret_key: str, bucket_name: str, prefix_path: str):

        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=access_secret_key
        )

        self.s3 = session.client('s3')
        self.bucket_name = bucket_name
        self.prefix_path = prefix_path

    def upload_string_to_s3(self, content: str, s3_key: str) -> str:

        # Upload the content to S3
        if self.prefix_path:
            s3_key = f"{self.prefix_path}{s3_key}"

        self.s3.put_object(Body=content, Bucket=self.bucket_name,
                           Key=s3_key, ACL='public-read', ContentType='text/html')

        # Generate a publicly accessible link
        s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"

        return s3_url

    def upload_file_to_s3(self, file_path: str, s3_key: str, content_type: str) -> str:

        # Upload the file to S3
        if self.prefix_path:
            s3_key = f"{self.prefix_path}{s3_key}"

        # use boto3 s3 client to upload file_path to s3_key
        self.s3.upload_file(
            Filename=file_path, Bucket=self.bucket_name,
            Key=s3_key, ExtraArgs={'ACL':'public-read', 'ContentType': content_type})

        # Generate a publicly accessible link
        s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"

        return s3_url
