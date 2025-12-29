#!/usr/bin/env python3
"""
Approval System - Human-in-the-Loop Agent

Provides approval workflows for high-stakes agent actions.

Usage:
    python main.py --dashboard
    python main.py --request --agent my-agent --action risky-action
"""

import os
import sys
import yaml
import json
import sqlite3
import logging
import argparse
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/approval-system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('approval-system')


class RequestStatus(Enum):
    """Approval request status"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RiskLevel(Enum):
    """Risk level enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalRequest:
    """Approval request data"""
    id: str
    agent: str
    action: str
    details: Dict[str, Any]
    risk_level: str
    category: Optional[str]
    status: RequestStatus
    created_at: str
    timeout_at: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    denial_reason: Optional[str] = None
    comment: Optional[str] = None


class ApprovalDatabase:
    """Manages approval requests database"""
    
    def __init__(self, db_path: str = "./data/approvals.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY,
                agent TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                risk_level TEXT NOT NULL,
                category TEXT,
                status TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                timeout_at DATETIME,
                approved_by TEXT,
                approved_at DATETIME,
                denial_reason TEXT,
                comment TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action TEXT,
                user TEXT,
                details TEXT,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_requests_status 
            ON requests(status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_requests_agent 
            ON requests(agent)
        ''')
        
        conn.commit()
        conn.close()
    
    def create_request(self, request: ApprovalRequest) -> str:
        """Create a new approval request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO requests (
                id, agent, action, details, risk_level, category,
                status, created_at, timeout_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.id, request.agent, request.action,
            json.dumps(request.details), request.risk_level,
            request.category, request.status.value,
            request.created_at, request.timeout_at
        ))
        
        # Audit log
        cursor.execute('''
            INSERT INTO audit_log (request_id, action, details)
            VALUES (?, ?, ?)
        ''', (request.id, 'created', json.dumps({'risk_level': request.risk_level})))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created approval request: {request.id}")
        return request.id
    
    def get_request(self, request_id: str) -> Optional[Dict]:
        """Get approval request by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM requests WHERE id = ?', (request_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data = dict(row)
            data['details'] = json.loads(data['details']) if data['details'] else {}
            return data
        return None
    
    def get_pending_requests(self) -> List[Dict]:
        """Get all pending approval requests"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM requests WHERE status = 'pending' ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()
        
        requests = []
        for row in rows:
            data = dict(row)
            data['details'] = json.loads(data['details']) if data['details'] else {}
            requests.append(data)
        
        return requests
    
    def update_status(self, request_id: str, status: RequestStatus,
                     approved_by: str = None, comment: str = None,
                     denial_reason: str = None):
        """Update request status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = ['status = ?']
        params = [status.value]
        
        if status == RequestStatus.APPROVED:
            update_fields.append('approved_by = ?')
            update_fields.append('approved_at = ?')
            params.extend([approved_by, datetime.now().isoformat()])
        
        if comment:
            update_fields.append('comment = ?')
            params.append(comment)
        
        if denial_reason:
            update_fields.append('denial_reason = ?')
            params.append(denial_reason)
        
        params.append(request_id)
        
        cursor.execute(
            f"UPDATE requests SET {', '.join(update_fields)} WHERE id = ?",
            params
        )
        
        # Audit log
        cursor.execute('''
            INSERT INTO audit_log (request_id, action, user, details)
            VALUES (?, ?, ?, ?)
        ''', (
            request_id, status.value, approved_by,
            json.dumps({'comment': comment, 'denial_reason': denial_reason})
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated request {request_id}: {status.value}")
    
    def get_history(self, days: int = 30, limit: int = 100) -> List[Dict]:
        """Get approval history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT * FROM requests 
            WHERE created_at >= ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (start_date, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            data = dict(row)
            data['details'] = json.loads(data['details']) if data['details'] else {}
            history.append(data)
        
        return history


class ApprovalSystem:
    """Main approval system class"""
    
    def __init__(self, config_path: str = "agent.yaml"):
        self.config = self._load_config(config_path)
        self.db = ApprovalDatabase()
        self.watchers = {}
        self.timeout_thread = None
        self.running = False
        logger.info("Approval System initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _generate_request_id(self, agent: str, action: str) -> str:
        """Generate unique request ID"""
        timestamp = int(time.time() * 1000)
        data = f"{agent}:{action}:{timestamp}"
        hash_part = hashlib.md5(data.encode()).hexdigest()[:8]
        return f"AR-{timestamp}-{hash_part}"
    
    def _calculate_timeout(self, risk_level: str) -> datetime:
        """Calculate timeout based on risk level"""
        risk_config = self.config.get('settings', {}).get('risk_levels', {}).get(risk_level, {})
        timeout_seconds = risk_config.get('timeout', 1800)
        return datetime.now() + timedelta(seconds=timeout_seconds)
    
    def request_approval(
        self,
        agent: str,
        action: str,
        details: Dict[str, Any],
        risk_level: str = "medium",
        category: str = None,
        timeout: int = None
    ) -> str:
        """Request approval for an action"""
        request_id = self._generate_request_id(agent, action)
        
        if timeout:
            timeout_at = datetime.now() + timedelta(seconds=timeout)
        else:
            timeout_at = self._calculate_timeout(risk_level)
        
        request = ApprovalRequest(
            id=request_id,
            agent=agent,
            action=action,
            details=details,
            risk_level=risk_level,
            category=category,
            status=RequestStatus.PENDING,
            created_at=datetime.now().isoformat(),
            timeout_at=timeout_at.isoformat()
        )
        
        self.db.create_request(request)
        
        # Send notifications
        self._notify_request(request)
        
        return request_id
    
    def _notify_request(self, request: ApprovalRequest):
        """Send notifications for new request"""
        # Log notification
        logger.info(
            f"Approval requested: {request.agent} - {request.action} "
            f"(Risk: {request.risk_level})"
        )
        
        # Email notification (if configured)
        # SMS notification (if configured)
        # Slack notification (if configured)
        pass
    
    def approve(
        self,
        request_id: str,
        approver: str,
        comment: str = None
    ) -> bool:
        """Approve a request"""
        request = self.db.get_request(request_id)
        
        if not request:
            logger.error(f"Request not found: {request_id}")
            return False
        
        if request['status'] != RequestStatus.PENDING.value:
            logger.warning(f"Request not pending: {request_id}")
            return False
        
        self.db.update_status(
            request_id,
            RequestStatus.APPROVED,
            approved_by=approver,
            comment=comment
        )
        
        logger.info(f"Request approved: {request_id} by {approver}")
        return True
    
    def deny(
        self,
        request_id: str,
        approver: str,
        reason: str = None
    ) -> bool:
        """Deny a request"""
        request = self.db.get_request(request_id)
        
        if not request:
            logger.error(f"Request not found: {request_id}")
            return False
        
        if request['status'] != RequestStatus.PENDING.value:
            logger.warning(f"Request not pending: {request_id}")
            return False
        
        self.db.update_status(
            request_id,
            RequestStatus.DENIED,
            approved_by=approver,
            denial_reason=reason
        )
        
        logger.info(f"Request denied: {request_id} by {approver}")
        return True
    
    def get_status(self, request_id: str) -> Optional[Dict]:
        """Get request status"""
        return self.db.get_request(request_id)
    
    def wait_for_approval(
        self,
        request_id: str,
        timeout: int = None,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """Wait for approval decision"""
        request = self.db.get_request(request_id)
        
        if not request:
            return {'status': 'error', 'message': 'Request not found'}
        
        timeout_at = datetime.fromisoformat(request['timeout_at'])
        
        while datetime.now() < timeout_at:
            request = self.db.get_request(request_id)
            
            if request['status'] == RequestStatus.APPROVED.value:
                return {
                    'status': 'approved',
                    'approved_by': request['approved_by'],
                    'approved_at': request['approved_at'],
                    'comment': request['comment']
                }
            
            elif request['status'] == RequestStatus.DENIED.value:
                return {
                    'status': 'denied',
                    'denied_by': request['approved_by'],
                    'reason': request['denial_reason']
                }
            
            elif request['status'] in [RequestStatus.EXPIRED.value, RequestStatus.CANCELLED.value]:
                return {'status': request['status']}
            
            time.sleep(poll_interval)
        
        # Timeout expired
        self.db.update_status(request_id, RequestStatus.EXPIRED)
        return {'status': 'expired'}
    
    def check_timeouts(self):
        """Check for expired requests"""
        pending = self.db.get_pending_requests()
        now = datetime.now()
        
        for request in pending:
            timeout_at = datetime.fromisoformat(request['timeout_at'])
            if now >= timeout_at:
                self.db.update_status(request['id'], RequestStatus.EXPIRED)
                logger.warning(f"Request expired: {request['id']}")
    
    def start_timeout_monitor(self):
        """Start background timeout monitor"""
        def monitor():
            while self.running:
                self.check_timeouts()
                time.sleep(60)  # Check every minute
        
        self.running = True
        self.timeout_thread = threading.Thread(target=monitor, daemon=True)
        self.timeout_thread.start()
        logger.info("Timeout monitor started")
    
    def stop(self):
        """Stop the approval system"""
        self.running = False
        if self.timeout_thread:
            self.timeout_thread.join(timeout=5)
        logger.info("Approval System stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Approval System - Human-in-the-Loop')
    parser.add_argument('--init', action='store_true', help='Initialize system')
    parser.add_argument('--dashboard', action='store_true', help='Start web dashboard')
    parser.add_argument('--request', action='store_true', help='Create approval request')
    parser.add_argument('--agent', type=str, help='Agent name')
    parser.add_argument('--action', type=str, help='Action name')
    parser.add_argument('--risk', type=str, default='medium', help='Risk level')
    parser.add_argument('--approve', type=str, help='Approve request ID')
    parser.add_argument('--deny', type=str, help='Deny request ID')
    parser.add_argument('--status', type=str, help='Check request status')
    parser.add_argument('--list', action='store_true', help='List pending requests')
    
    args = parser.parse_args()
    
    # Create directories
    for directory in ['data', 'logs', 'reports']:
        Path(directory).mkdir(exist_ok=True)
    
    # Initialize system
    approval = ApprovalSystem()
    
    if args.init:
        print("Approval System initialized")
        print("\nStart dashboard: python main.py --dashboard")
        return
    
    if args.dashboard:
        print("Starting dashboard...")
        print("Note: Requires Streamlit. Run: pip install streamlit")
        print("Then: streamlit run dashboard.py")
        return
    
    if args.request:
        if not args.agent or not args.action:
            print("Error: --agent and --action required")
            return
        
        request_id = approval.request_approval(
            agent=args.agent,
            action=args.action,
            details={'source': 'cli'},
            risk_level=args.risk
        )
        print(f"Approval request created: {request_id}")
    
    elif args.approve:
        if approval.approve(args.approve, approver="cli-user"):
            print(f"Request approved: {args.approve}")
        else:
            print(f"Failed to approve: {args.approve}")
    
    elif args.deny:
        if approval.deny(args.deny, approver="cli-user", reason="Denied via CLI"):
            print(f"Request denied: {args.deny}")
        else:
            print(f"Failed to deny: {args.deny}")
    
    elif args.status:
        status = approval.get_status(args.status)
        if status:
            print(json.dumps(status, indent=2))
        else:
            print(f"Request not found: {args.status}")
    
    elif args.list:
        pending = approval.db.get_pending_requests()
        print(f"\nPending Approval Requests: {len(pending)}\n")
        for req in pending:
            print(f"ID: {req['id']}")
            print(f"  Agent: {req['agent']}")
            print(f"  Action: {req['action']}")
            print(f"  Risk: {req['risk_level']}")
            print(f"  Created: {req['created_at']}")
            print()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()