#!/usr/bin/env python3
"""
Code Auditor - Security Sentinel Agent

Autonomous security scanning agent that monitors codebases for:
- Security vulnerabilities
- Exposed secrets (API keys, passwords)
- Code quality issues
- Dependency vulnerabilities

Usage:
    python main.py --scan /path/to/code
    python main.py --watch /path/to/code
"""

import os
import sys
import re
import sqlite3
import json
import yaml
import hashlib
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/code-auditor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('code-auditor')


@dataclass
class SecurityFinding:
    """Represents a security finding"""
    file_path: str
    line_number: int
    severity: str  # critical, high, medium, low
    issue_type: str
    description: str
    recommendation: str
    code_snippet: str = ""
    cwe_id: str = ""
    confidence: str = "high"


class SecurityDatabase:
    """Manages security findings database"""
    
    def __init__(self, db_path: str = "./data/security.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                path TEXT NOT NULL,
                duration_seconds REAL,
                files_scanned INTEGER,
                issues_found INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER,
                file_path TEXT NOT NULL,
                line_number INTEGER,
                severity TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                description TEXT,
                recommendation TEXT,
                code_snippet TEXT,
                cwe_id TEXT,
                confidence TEXT,
                file_hash TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME,
                FOREIGN KEY (scan_id) REFERENCES scans(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_findings_severity 
            ON findings(severity)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_findings_file 
            ON findings(file_path)
        ''')
        
        conn.commit()
        conn.close()
    
    def start_scan(self, path: str) -> int:
        """Start a new scan and return scan ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO scans (path, files_scanned, issues_found) VALUES (?, 0, 0)',
            (path,)
        )
        scan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return scan_id
    
    def add_finding(self, scan_id: int, finding: SecurityFinding):
        """Add a security finding to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate file hash for duplicate detection
        file_hash = hashlib.md5(
            f"{finding.file_path}:{finding.line_number}:{finding.issue_type}".encode()
        ).hexdigest()
        
        cursor.execute('''
            INSERT INTO findings (
                scan_id, file_path, line_number, severity, issue_type,
                description, recommendation, code_snippet, cwe_id, confidence, file_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            scan_id, finding.file_path, finding.line_number, finding.severity,
            finding.issue_type, finding.description, finding.recommendation,
            finding.code_snippet, finding.cwe_id, finding.confidence, file_hash
        ))
        
        conn.commit()
        conn.close()
    
    def complete_scan(self, scan_id: int, duration: float, files_scanned: int, issues_found: int):
        """Mark scan as complete with statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE scans 
            SET duration_seconds = ?, files_scanned = ?, issues_found = ?
            WHERE id = ?
        ''', (duration, files_scanned, issues_found, scan_id))
        conn.commit()
        conn.close()
    
    def get_findings(self, severity: str = None, limit: int = 100) -> List[Dict]:
        """Retrieve findings, optionally filtered by severity"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if severity:
            cursor.execute(
                'SELECT * FROM findings WHERE severity = ? AND resolved_at IS NULL ORDER BY id DESC LIMIT ?',
                (severity, limit)
            )
        else:
            cursor.execute(
                'SELECT * FROM findings WHERE resolved_at IS NULL ORDER BY id DESC LIMIT ?',
                (limit,)
            )
        
        findings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return findings


class SecretScanner:
    """Scans for hardcoded secrets and credentials"""
    
    def __init__(self, patterns: List[Dict]):
        self.patterns = patterns
        self.compiled_patterns = [
            {
                'name': p['name'],
                'regex': re.compile(p['pattern'], re.IGNORECASE),
                'severity': p['severity']
            }
            for p in patterns
        ]
    
    def scan_file(self, file_path: str) -> List[SecurityFinding]:
        """Scan a file for secrets"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in self.compiled_patterns:
                        if pattern['regex'].search(line):
                            finding = SecurityFinding(
                                file_path=file_path,
                                line_number=line_num,
                                severity=pattern['severity'],
                                issue_type='hardcoded_secret',
                                description=f"{pattern['name']} detected in source code",
                                recommendation="Move credentials to environment variables or secure vault",
                                code_snippet=line.strip(),
                                cwe_id="CWE-798"
                            )
                            findings.append(finding)
                            logger.warning(f"Secret found: {file_path}:{line_num} - {pattern['name']}")
        
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
        
        return findings


class VulnerabilityScanner:
    """Scans for common security vulnerabilities"""
    
    VULNERABILITY_PATTERNS = {
        'sql_injection': {
            'pattern': r'(execute|cursor)\s*\(\s*f?["\'].*%s.*["\']\s*%',
            'description': 'Potential SQL injection vulnerability',
            'recommendation': 'Use parameterized queries instead of string formatting',
            'cwe': 'CWE-89',
            'severity': 'critical'
        },
        'command_injection': {
            'pattern': r'(os\.system|subprocess\.call|eval)\s*\(.*input.*\)',
            'description': 'Potential command injection vulnerability',
            'recommendation': 'Validate and sanitize all user input, use allow-lists',
            'cwe': 'CWE-78',
            'severity': 'critical'
        },
        'path_traversal': {
            'pattern': r'open\s*\(.*\+.*\)',
            'description': 'Potential path traversal vulnerability',
            'recommendation': 'Validate file paths and use os.path.join()',
            'cwe': 'CWE-22',
            'severity': 'high'
        },
        'weak_crypto': {
            'pattern': r'(MD5|SHA1)\s*\(',
            'description': 'Use of weak cryptographic algorithm',
            'recommendation': 'Use SHA-256 or stronger algorithms',
            'cwe': 'CWE-327',
            'severity': 'medium'
        }
    }
    
    def scan_file(self, file_path: str) -> List[SecurityFinding]:
        """Scan a file for vulnerabilities"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    for vuln_type, vuln_info in self.VULNERABILITY_PATTERNS.items():
                        pattern = re.compile(vuln_info['pattern'], re.IGNORECASE)
                        if pattern.search(line):
                            finding = SecurityFinding(
                                file_path=file_path,
                                line_number=line_num,
                                severity=vuln_info['severity'],
                                issue_type=vuln_type,
                                description=vuln_info['description'],
                                recommendation=vuln_info['recommendation'],
                                code_snippet=line.strip(),
                                cwe_id=vuln_info['cwe']
                            )
                            findings.append(finding)
                            logger.warning(f"Vulnerability found: {file_path}:{line_num} - {vuln_type}")
        
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
        
        return findings


class CodeAuditor:
    """Main security auditor class"""
    
    def __init__(self, config_path: str = "agent.yaml"):
        self.config = self._load_config(config_path)
        self.db = SecurityDatabase()
        
        # Initialize scanners
        secret_patterns = self.config.get('settings', {}).get('secret_patterns', [])
        self.secret_scanner = SecretScanner(secret_patterns)
        self.vuln_scanner = VulnerabilityScanner()
        
        self.exclude_patterns = self.config.get('settings', {}).get('exclude_patterns', [])
        self.severity_threshold = self.config.get('settings', {}).get('severity_threshold', 'medium')
        
        logger.info("Code Auditor initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _should_exclude(self, file_path: str) -> bool:
        """Check if file should be excluded from scanning"""
        for pattern in self.exclude_patterns:
            if re.search(pattern.replace('*', '.*'), file_path):
                return True
        return False
    
    def scan_file(self, file_path: str) -> List[SecurityFinding]:
        """Scan a single file"""
        if self._should_exclude(file_path):
            return []
        
        findings = []
        findings.extend(self.secret_scanner.scan_file(file_path))
        findings.extend(self.vuln_scanner.scan_file(file_path))
        
        return findings
    
    def scan_directory(self, directory: str) -> Dict[str, Any]:
        """Scan entire directory"""
        logger.info(f"Starting security scan of {directory}")
        start_time = datetime.now()
        
        scan_id = self.db.start_scan(directory)
        all_findings = []
        files_scanned = 0
        
        # Walk directory tree
        for root, dirs, files in os.walk(directory):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d))]
            
            for file in files:
                # Only scan code files
                if file.endswith(('.py', '.js', '.java', '.go', '.rb', '.php', '.yaml', '.yml', '.json')):
                    file_path = os.path.join(root, file)
                    if not self._should_exclude(file_path):
                        findings = self.scan_file(file_path)
                        for finding in findings:
                            self.db.add_finding(scan_id, finding)
                            all_findings.append(finding)
                        files_scanned += 1
        
        # Complete scan
        duration = (datetime.now() - start_time).total_seconds()
        self.db.complete_scan(scan_id, duration, files_scanned, len(all_findings))
        
        # Generate summary
        summary = self._generate_summary(all_findings)
        logger.info(f"Scan complete: {summary}")
        
        return {
            'scan_id': scan_id,
            'duration': duration,
            'files_scanned': files_scanned,
            'total_findings': len(all_findings),
            'summary': summary,
            'findings': all_findings
        }
    
    def _generate_summary(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """Generate findings summary by severity"""
        summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for finding in findings:
            summary[finding.severity] = summary.get(finding.severity, 0) + 1
        return summary
    
    def generate_report(self, scan_id: int, format: str = 'json') -> str:
        """Generate scan report"""
        findings = self.db.get_findings()
        
        if format == 'json':
            report_path = f"./reports/scan-{scan_id}.json"
            with open(report_path, 'w') as f:
                json.dump([asdict(f) for f in findings], f, indent=2)
            return report_path
        
        elif format == 'html':
            # Generate HTML report
            report_path = f"./reports/scan-{scan_id}.html"
            html = self._generate_html_report(findings)
            with open(report_path, 'w') as f:
                f.write(html)
            return report_path
        
        return ""
    
    def _generate_html_report(self, findings: List[Dict]) -> str:
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Audit Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .critical {{ color: red; }}
                .high {{ color: orange; }}
                .medium {{ color: yellow; }}
                .low {{ color: green; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
            </style>
        </head>
        <body>
            <h1>Security Audit Report</h1>
            <p>Generated: {datetime.now().isoformat()}</p>
            <table>
                <tr>
                    <th>Severity</th>
                    <th>File</th>
                    <th>Line</th>
                    <th>Issue</th>
                    <th>Description</th>
                </tr>
        """
        
        for finding in findings:
            severity_class = finding['severity']
            html += f"""
                <tr>
                    <td class="{severity_class}">{finding['severity'].upper()}</td>
                    <td>{finding['file_path']}</td>
                    <td>{finding['line_number']}</td>
                    <td>{finding['issue_type']}</td>
                    <td>{finding['description']}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        return html


class FileWatchHandler(FileSystemEventHandler):
    """Handles file system events for monitoring"""
    
    def __init__(self, auditor: CodeAuditor):
        self.auditor = auditor
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.py', '.js', '.java', '.go')):
            logger.info(f"File modified: {event.src_path}")
            findings = self.auditor.scan_file(event.src_path)
            if findings:
                logger.warning(f"Found {len(findings)} issues in {event.src_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Code Auditor - Security Sentinel')
    parser.add_argument('--scan', type=str, help='Directory to scan')
    parser.add_argument('--watch', type=str, help='Directory to watch for changes')
    parser.add_argument('--config', type=str, default='agent.yaml', help='Config file')
    parser.add_argument('--report', type=str, choices=['json', 'html'], help='Generate report')
    parser.add_argument('--severity', type=str, choices=['critical', 'high', 'medium', 'low'])
    
    args = parser.parse_args()
    
    # Create directories
    for directory in ['logs', 'data', 'reports']:
        Path(directory).mkdir(exist_ok=True)
    
    # Initialize auditor
    auditor = CodeAuditor(args.config)
    
    if args.scan:
        # One-time scan
        results = auditor.scan_directory(args.scan)
        print(f"\nScan Results:")
        print(f"Files scanned: {results['files_scanned']}")
        print(f"Issues found: {results['total_findings']}")
        print(f"Summary: {results['summary']}")
        
        if args.report:
            report_path = auditor.generate_report(results['scan_id'], args.report)
            print(f"Report saved to: {report_path}")
    
    elif args.watch:
        # Continuous monitoring
        logger.info(f"Watching directory: {args.watch}")
        event_handler = FileWatchHandler(auditor)
        observer = Observer()
        observer.schedule(event_handler, args.watch, recursive=True)
        observer.start()
        
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()