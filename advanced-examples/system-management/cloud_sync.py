#!/usr/bin/env python3
"""
Cloud Sync - S3 Synchronization

Sync data to AWS S3 or other cloud storage.

Usage:
    python cloud_sync.py --sync-to-s3 --bucket my-bucket
"""

import os
import logging
import argparse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cloud-sync')


class CloudSync:
    """Cloud storage synchronization"""
    
    def __init__(self, provider: str = 's3'):
        self.provider = provider
        self.synced_files = 0
        self.synced_size = 0
    
    def sync_to_s3(self, local_path: str, bucket: str, prefix: str = ''):
        """Sync local files to S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            logger.error("boto3 not installed. Run: pip install boto3")
            return
        
        logger.info(f"Syncing {local_path} to s3://{bucket}/{prefix}")
        
        s3_client = boto3.client('s3')
        local_path_obj = Path(local_path)
        
        if not local_path_obj.exists():
            logger.error(f"Path does not exist: {local_path}")
            return
        
        for root, dirs, files in os.walk(local_path):
            for file in files:
                local_file = Path(root) / file
                relative_path = local_file.relative_to(local_path_obj)
                s3_key = f"{prefix}/{relative_path}" if prefix else str(relative_path)
                
                try:
                    logger.info(f"Uploading: {local_file} -> s3://{bucket}/{s3_key}")
                    s3_client.upload_file(str(local_file), bucket, s3_key)
                    
                    self.synced_files += 1
                    self.synced_size += local_file.stat().st_size
                
                except ClientError as e:
                    logger.error(f"Error uploading {local_file}: {e}")
        
        logger.info(f"Sync complete: {self.synced_files} files, {self.synced_size / (1024*1024):.2f} MB")
    
    def restore_from_s3(self, bucket: str, prefix: str, local_path: str):
        """Restore files from S3"""
        try:
            import boto3
        except ImportError:
            logger.error("boto3 not installed. Run: pip install boto3")
            return
        
        logger.info(f"Restoring from s3://{bucket}/{prefix} to {local_path}")
        
        s3_client = boto3.client('s3')
        local_path_obj = Path(local_path)
        local_path_obj.mkdir(parents=True, exist_ok=True)
        
        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    s3_key = obj['Key']
                    relative_path = s3_key[len(prefix):].lstrip('/')
                    local_file = local_path_obj / relative_path
                    
                    local_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    logger.info(f"Downloading: s3://{bucket}/{s3_key} -> {local_file}")
                    s3_client.download_file(bucket, s3_key, str(local_file))
                    
                    self.synced_files += 1
            
            logger.info(f"Restore complete: {self.synced_files} files")
        
        except Exception as e:
            logger.error(f"Error restoring from S3: {e}")


def main():
    parser = argparse.ArgumentParser(description='Cloud Sync - S3 Synchronization')
    parser.add_argument('--sync-to-s3', action='store_true', help='Sync to S3')
    parser.add_argument('--restore-from-s3', action='store_true', help='Restore from S3')
    parser.add_argument('--bucket', type=str, required=True, help='S3 bucket name')
    parser.add_argument('--prefix', type=str, default='', help='S3 prefix/path')
    parser.add_argument('--local-path', type=str, default='./data', help='Local path')
    
    args = parser.parse_args()
    
    sync = CloudSync()
    
    if args.sync_to_s3:
        sync.sync_to_s3(args.local_path, args.bucket, args.prefix)
    
    elif args.restore_from_s3:
        sync.restore_from_s3(args.bucket, args.prefix, args.local_path)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()