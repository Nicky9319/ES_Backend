import boto3
from botocore.client import Config

minio_endpoint = "http://localhost:9000"
access_key = "minioadmin"
secret_key = "minioadmin123"
bucket_name = "mybucket"
filename = "test.txt"
object_name = "uploaded_test.txt"  # name it will have inside MinIO

def connect_to_minio():
    # Create and return the S3 client
    return boto3.client(
        "s3",
        endpoint_url=minio_endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )

def ensure_bucket_exists(client, bucket):
    existing = client.list_buckets()
    if not any(b["Name"] == bucket for b in existing.get("Buckets", [])):
        client.create_bucket(Bucket=bucket)

def upload_file(client, file_path, bucket, key):
    client.upload_file(Filename=file_path, Bucket=bucket, Key=key)

def list_bucket_files(client, bucket):
    result = client.list_objects_v2(Bucket=bucket)
    return [obj["Key"] for obj in result.get("Contents", [])]

def retrieve_file(client, bucket, key, download_path):
    client.download_file(Bucket=bucket, Key=key, Filename=download_path)

def main():
    client = connect_to_minio()
    ensure_bucket_exists(client, bucket_name)
    
    upload_file(client, filename, bucket_name, object_name)
    print(f"Uploaded '{filename}' as '{object_name}' in bucket '{bucket_name}'.")
    
    objects = list_bucket_files(client, bucket_name)
    if objects:
        print("Objects in bucket:")
        for obj in objects:
            print(obj)
    else:
        print("Bucket is empty.")
    
    # Example of how to retrieve a file (download it as 'downloaded_test.txt')
    # retrieve_file(client, bucket_name, object_name, "downloaded_test.txt")
    # print(f"Downloaded '{object_name}' to 'downloaded_test.txt'.")

if __name__ == "__main__":
    main()
