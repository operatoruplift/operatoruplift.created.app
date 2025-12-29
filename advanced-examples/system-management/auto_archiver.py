#!/usr/bin/env python3
"""
Auto-Archiver - Automatic File Archiving

Automatically archives old files based on age and policies.

Usage:
    python auto_archiver.py --days 90 --path /workspace
"""

import os
import shutil
import gzip
import tarfile
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auto-archiver')


class AutoArchiver:
    """Automatic file archiver"""
    
    def __init__(self, destination: str = './archives'):
        self.destination = Path(destination)
        self.destination.mkdir(parents=True, exist_ok=True)
        self.archived_count = 0
        self.archived_size = 0
    
    def archive_old_files(self, path: str, days: int, compress: bool = True):
        """Archive files older than specified days"""
        logger.info(f"Scanning {path} for files older than {days} days")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        path_obj = Path(path)
        
        if not path_obj.exists():
            logger.error(f"Path does not exist: {path}")
            return
        
        files_to_archive = []
        
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                
                try:
                    # Get modification time
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if mtime < cutoff_date:
                        files_to_archive.append(file_path)
                
                except Exception as e:
                    logger.error(f"Error checking file {file_path}: {e}")
        
        logger.info(f"Found {len(files_to_archive)} files to archive")
        
        if files_to_archive:
            self._create_archive(files_to_archive, compress)
    
    def _create_archive(self, files: list, compress: bool):
        """Create archive from file list"""
        archive_name = f"archive-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        if compress:
            archive_path = self.destination / f"{archive_name}.tar.gz"
            
            with tarfile.open(archive_path, "w:gz") as tar:
                for file_path in files:
                    try:
                        tar.add(file_path, arcname=file_path.name)
                        size = file_path.stat().st_size
                        self.archived_size += size
                        logger.info(f"Archived: {file_path}")
                    except Exception as e:
                        logger.error(f"Error archiving {file_path}: {e}")
            
            logger.info(f"Created archive: {archive_path}")
        
        else:
            archive_dir = self.destination / archive_name
            archive_dir.mkdir(exist_ok=True)
            
            for file_path in files:
                try:
                    dest = archive_dir / file_path.name
                    shutil.move(str(file_path), str(dest))
                    logger.info(f"Moved: {file_path} -> {dest}")
                except Exception as e:
                    logger.error(f"Error moving {file_path}: {e}")
        
        self.archived_count = len(files)
        
        # Delete original files
        self._delete_archived_files(files)
    
    def _delete_archived_files(self, files: list):
        """Delete files after archiving"""
        for file_path in files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Deleted: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Auto-Archiver - Automatic File Archiving')
    parser.add_argument('--path', type=str, required=True, help='Path to scan')
    parser.add_argument('--days', type=int, default=90, help='Archive files older than N days')
    parser.add_argument('--compress', action='store_true', help='Compress archives')
    parser.add_argument('--destination', type=str, default='./archives', help='Archive destination')
    
    args = parser.parse_args()
    
    archiver = AutoArchiver(destination=args.destination)
    archiver.archive_old_files(args.path, args.days, args.compress)
    
    print(f"\nArchiving complete:")
    print(f"  Files archived: {archiver.archived_count}")
    print(f"  Total size: {archiver.archived_size / (1024*1024):.2f} MB")


if __name__ == '__main__':
    main()