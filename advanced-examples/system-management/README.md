# System Management - Essential System Tools

## Overview

The System Management suite provides essential tools for managing UPLIFT agents including emergency kill switches, automatic file archiving, cloud synchronization, and system health monitoring.

## Components

### 1. **Emergency Kill Switch**
Immediately stop all agents in critical situations.

### 2. **Auto-Archiver**
Automatically archive old files based on policies.

### 3. **Cloud Sync**
Sync data to S3 or other cloud storage.

### 4. **System Health Monitor**
Monitor overall system health and resources.

## Installation

```bash
pip install -r requirements.txt
mkdir -p data logs archives
```

## Usage

### Kill Switch

```bash
# Emergency stop all agents
python kill_switch.py --emergency-stop

# Stop specific agent
python kill_switch.py --stop-agent code-auditor

# Graceful shutdown all
python kill_switch.py --graceful-shutdown
```

### Auto-Archiver

```bash
# Archive files older than 90 days
python auto_archiver.py --days 90 --path /workspace

# Archive and compress
python auto_archiver.py --days 30 --compress --path /logs

# Move to archive location
python auto_archiver.py --days 60 --destination /archives
```

### Cloud Sync

```bash
# Sync to S3
python cloud_sync.py --sync-to-s3 --bucket my-bucket

# Sync specific directory
python cloud_sync.py --sync ./data --bucket my-bucket --prefix uplift/

# Restore from S3
python cloud_sync.py --restore-from-s3 --bucket my-bucket
```

## Documentation

See individual component READMEs in subdirectories.

---

**Manage your system effectively. ⚙️**