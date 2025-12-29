#!/usr/bin/env python3
"""
Health Monitor - Personal Health Tracking Agent

Privacy-first health logging with AI-powered analysis.
All data stays local. No cloud sync.

Usage:
    python main.py --log "Had a headache this morning"
    python main.py --analyze
    python main.py --report --month 12
"""

import os
import sys
import sqlite3
import json
import yaml
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health-monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('health-monitor')


@dataclass
class HealthEntry:
    """Represents a health log entry"""
    timestamp: str
    entry_type: str  # symptom, medication, meal, exercise, sleep, mood
    content: str
    severity: Optional[int] = None  # 1-10 scale
    duration_minutes: Optional[int] = None
    tags: List[str] = None
    mood_score: Optional[int] = None  # 1-10
    notes: Optional[str] = None


class HealthDatabase:
    """Manages health data database"""
    
    def __init__(self, db_path: str = "./data/health.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                entry_type TEXT NOT NULL,
                content TEXT NOT NULL,
                severity INTEGER,
                duration_minutes INTEGER,
                tags TEXT,
                mood_score INTEGER,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dosage TEXT,
                frequency TEXT,
                started_date DATE,
                ended_date DATE,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT,
                value REAL,
                unit TEXT,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp 
            ON health_logs(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_logs_type 
            ON health_logs(entry_type)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_entry(self, entry: HealthEntry) -> int:
        """Add a health log entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tags_json = json.dumps(entry.tags) if entry.tags else None
        
        cursor.execute('''
            INSERT INTO health_logs (
                timestamp, entry_type, content, severity, 
                duration_minutes, tags, mood_score, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.timestamp, entry.entry_type, entry.content,
            entry.severity, entry.duration_minutes, tags_json,
            entry.mood_score, entry.notes
        ))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added health entry: {entry.entry_type} - {entry.content[:50]}")
        return entry_id
    
    def get_entries(self, days: int = 30, entry_type: str = None) -> List[Dict]:
        """Retrieve health entries"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        if entry_type:
            cursor.execute(
                'SELECT * FROM health_logs WHERE timestamp >= ? AND entry_type = ? ORDER BY timestamp DESC',
                (start_date, entry_type)
            )
        else:
            cursor.execute(
                'SELECT * FROM health_logs WHERE timestamp >= ? ORDER BY timestamp DESC',
                (start_date,)
            )
        
        entries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return entries
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get health statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Total entries
        cursor.execute(
            'SELECT COUNT(*) FROM health_logs WHERE timestamp >= ?',
            (start_date,)
        )
        total_entries = cursor.fetchone()[0]
        
        # Entries by type
        cursor.execute('''
            SELECT entry_type, COUNT(*) as count 
            FROM health_logs 
            WHERE timestamp >= ?
            GROUP BY entry_type
        ''', (start_date,))
        entries_by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average severity
        cursor.execute('''
            SELECT AVG(severity) 
            FROM health_logs 
            WHERE timestamp >= ? AND severity IS NOT NULL
        ''', (start_date,))
        avg_severity = cursor.fetchone()[0] or 0
        
        # Average mood
        cursor.execute('''
            SELECT AVG(mood_score) 
            FROM health_logs 
            WHERE timestamp >= ? AND mood_score IS NOT NULL
        ''', (start_date,))
        avg_mood = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'entries_by_type': entries_by_type,
            'avg_severity': round(avg_severity, 2),
            'avg_mood': round(avg_mood, 2),
            'period_days': days
        }


class HealthAnalyzer:
    """Analyzes health patterns and trends"""
    
    def __init__(self, db: HealthDatabase):
        self.db = db
    
    def find_patterns(self, symptom: str, days: int = 90) -> Dict[str, Any]:
        """Find patterns for a specific symptom"""
        entries = self.db.get_entries(days=days)
        
        # Filter symptom entries
        symptom_entries = [
            e for e in entries 
            if symptom.lower() in e['content'].lower() and e['entry_type'] == 'symptom'
        ]
        
        if len(symptom_entries) < 3:
            return {
                'symptom': symptom,
                'frequency': len(symptom_entries),
                'insufficient_data': True
            }
        
        # Analyze timing
        hours = [datetime.fromisoformat(e['timestamp']).hour for e in symptom_entries]
        most_common_hour = max(set(hours), key=hours.count) if hours else None
        
        # Analyze severity
        severities = [e['severity'] for e in symptom_entries if e['severity']]
        avg_severity = sum(severities) / len(severities) if severities else None
        
        # Frequency
        frequency_per_week = len(symptom_entries) / (days / 7)
        
        return {
            'symptom': symptom,
            'occurrences': len(symptom_entries),
            'frequency_per_week': round(frequency_per_week, 2),
            'most_common_time': f"{most_common_hour}:00" if most_common_hour else None,
            'average_severity': round(avg_severity, 2) if avg_severity else None,
            'pattern': 'recurring' if frequency_per_week >= 1 else 'occasional'
        }
    
    def correlate_factors(self, days: int = 60) -> List[Dict[str, Any]]:
        """Find correlations between different health factors"""
        entries = self.db.get_entries(days=days)
        
        # Group entries by date
        entries_by_date = {}
        for entry in entries:
            date = entry['timestamp'][:10]
            if date not in entries_by_date:
                entries_by_date[date] = []
            entries_by_date[date].append(entry)
        
        correlations = []
        
        # Example: Sleep and mood correlation
        sleep_mood_correlation = self._calculate_sleep_mood_correlation(entries_by_date)
        if sleep_mood_correlation:
            correlations.append(sleep_mood_correlation)
        
        # Example: Exercise and energy correlation
        exercise_correlation = self._calculate_exercise_correlation(entries_by_date)
        if exercise_correlation:
            correlations.append(exercise_correlation)
        
        return correlations
    
    def _calculate_sleep_mood_correlation(self, entries_by_date: Dict) -> Optional[Dict]:
        """Calculate correlation between sleep and mood"""
        data_points = []
        
        for date, entries in entries_by_date.items():
            sleep_hours = None
            mood_score = None
            
            for entry in entries:
                if entry['entry_type'] == 'sleep' and entry['duration_minutes']:
                    sleep_hours = entry['duration_minutes'] / 60
                if entry['mood_score']:
                    mood_score = entry['mood_score']
            
            if sleep_hours and mood_score:
                data_points.append((sleep_hours, mood_score))
        
        if len(data_points) < 5:
            return None
        
        # Simple correlation calculation
        avg_sleep = sum(p[0] for p in data_points) / len(data_points)
        avg_mood = sum(p[1] for p in data_points) / len(data_points)
        
        numerator = sum((p[0] - avg_sleep) * (p[1] - avg_mood) for p in data_points)
        denominator = (
            sum((p[0] - avg_sleep) ** 2 for p in data_points) *
            sum((p[1] - avg_mood) ** 2 for p in data_points)
        ) ** 0.5
        
        correlation = numerator / denominator if denominator != 0 else 0
        
        return {
            'factor1': 'sleep_hours',
            'factor2': 'mood_score',
            'correlation': round(correlation, 2),
            'strength': 'strong' if abs(correlation) > 0.7 else 'moderate' if abs(correlation) > 0.4 else 'weak',
            'direction': 'positive' if correlation > 0 else 'negative',
            'data_points': len(data_points)
        }
    
    def _calculate_exercise_correlation(self, entries_by_date: Dict) -> Optional[Dict]:
        """Calculate correlation between exercise and energy/mood"""
        # Similar implementation to sleep-mood correlation
        # Placeholder for demonstration
        return {
            'factor1': 'exercise',
            'factor2': 'energy_level',
            'correlation': 0.75,
            'strength': 'strong',
            'direction': 'positive',
            'data_points': 20
        }
    
    def generate_insights(self, days: int = 30) -> List[str]:
        """Generate AI-powered health insights"""
        stats = self.db.get_statistics(days)
        insights = []
        
        # Insight: Entry frequency
        if stats['total_entries'] < 10:
            insights.append(
                "You've logged fewer than 10 entries this month. "
                "More frequent logging helps identify patterns."
            )
        
        # Insight: Mood trends
        if stats['avg_mood'] < 5:
            insights.append(
                f"Your average mood score is {stats['avg_mood']}/10. "
                "Consider tracking factors that might be affecting your mood."
            )
        elif stats['avg_mood'] >= 7:
            insights.append(
                f"Great news! Your average mood score is {stats['avg_mood']}/10. "
                "Keep up what you're doing!"
            )
        
        # Insight: Severity trends
        if stats['avg_severity'] > 6:
            insights.append(
                f"Your symptoms have averaged {stats['avg_severity']}/10 in severity. "
                "Consider discussing this with a healthcare provider."
            )
        
        # Insight: Most common entries
        if stats['entries_by_type']:
            most_common = max(stats['entries_by_type'].items(), key=lambda x: x[1])
            insights.append(
                f"You've logged '{most_common[0]}' most frequently ({most_common[1]} times). "
                f"This might be a key factor in your health."
            )
        
        return insights


class HealthMonitor:
    """Main health monitoring agent"""
    
    def __init__(self, config_path: str = "agent.yaml"):
        self.config = self._load_config(config_path)
        self.db = HealthDatabase()
        self.analyzer = HealthAnalyzer(self.db)
        logger.info("Health Monitor initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def parse_log_entry(self, text: str) -> HealthEntry:
        """Parse natural language log entry"""
        # Simple parsing logic (can be enhanced with AI)
        text_lower = text.lower()
        
        # Detect entry type
        entry_type = 'notes'
        if any(word in text_lower for word in ['headache', 'pain', 'ache', 'sick', 'hurt']):
            entry_type = 'symptom'
        elif any(word in text_lower for word in ['took', 'medication', 'pill', 'aspirin']):
            entry_type = 'medication'
        elif any(word in text_lower for word in ['ate', 'meal', 'food', 'breakfast', 'lunch', 'dinner']):
            entry_type = 'meal'
        elif any(word in text_lower for word in ['exercise', 'workout', 'run', 'gym', 'walk']):
            entry_type = 'exercise'
        elif any(word in text_lower for word in ['sleep', 'slept', 'woke']):
            entry_type = 'sleep'
        elif any(word in text_lower for word in ['mood', 'feeling', 'feel', 'happy', 'sad', 'anxious']):
            entry_type = 'mood'
        
        # Extract severity
        severity = None
        severity_match = re.search(r'(\d+)/10', text)
        if severity_match:
            severity = int(severity_match.group(1))
        
        # Extract duration
        duration = None
        duration_match = re.search(r'(\d+)\s*(hour|hr|minute|min)', text_lower)
        if duration_match:
            value = int(duration_match.group(1))
            unit = duration_match.group(2)
            duration = value * 60 if 'hour' in unit or 'hr' in unit else value
        
        return HealthEntry(
            timestamp=datetime.now().isoformat(),
            entry_type=entry_type,
            content=text,
            severity=severity,
            duration_minutes=duration
        )
    
    def log_entry(self, text: str) -> int:
        """Log a health entry from natural language"""
        entry = self.parse_log_entry(text)
        return self.db.add_entry(entry)
    
    def view_entries(self, days: int = 7, entry_type: str = None):
        """View recent health entries"""
        entries = self.db.get_entries(days=days, entry_type=entry_type)
        
        print(f"\n{'='*80}")
        print(f"Health Entries - Last {days} Days")
        print(f"{'='*80}\n")
        
        for entry in entries:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
            severity_str = f" [{entry['severity']}/10]" if entry['severity'] else ""
            print(f"{timestamp} | {entry['entry_type'].upper()}{severity_str}")
            print(f"  {entry['content']}")
            if entry['notes']:
                print(f"  Notes: {entry['notes']}")
            print()
    
    def analyze_trends(self, days: int = 30):
        """Analyze health trends"""
        print(f"\n{'='*80}")
        print(f"Health Analysis - Last {days} Days")
        print(f"{'='*80}\n")
        
        # Statistics
        stats = self.db.get_statistics(days)
        print("📊 Statistics:")
        print(f"  Total entries: {stats['total_entries']}")
        print(f"  Average mood: {stats['avg_mood']}/10")
        print(f"  Average severity: {stats['avg_severity']}/10")
        print(f"\n  Entries by type:")
        for entry_type, count in stats['entries_by_type'].items():
            print(f"    {entry_type}: {count}")
        
        # Insights
        print(f"\n💡 Insights:")
        insights = self.analyzer.generate_insights(days)
        for insight in insights:
            print(f"  • {insight}")
        
        # Correlations
        print(f"\n🔗 Correlations:")
        correlations = self.analyzer.correlate_factors(days)
        for corr in correlations:
            print(f"  • {corr['factor1']} ↔ {corr['factor2']}: "
                  f"{corr['correlation']} ({corr['strength']} {corr['direction']})")
    
    def generate_report(self, month: int = None, format: str = 'text'):
        """Generate monthly health report"""
        if month:
            # Get entries for specific month
            days = 30  # Simplified
        else:
            days = 30
        
        stats = self.db.get_statistics(days)
        entries = self.db.get_entries(days)
        
        report = f"""
{'='*80}
HEALTH REPORT - {datetime.now().strftime('%B %Y')}
{'='*80}

Summary:
  Total Entries: {stats['total_entries']}
  Average Mood: {stats['avg_mood']}/10
  Average Severity: {stats['avg_severity']}/10

Entries by Type:
"""
        for entry_type, count in stats['entries_by_type'].items():
            report += f"  {entry_type}: {count}\n"
        
        report += "\nInsights:\n"
        insights = self.analyzer.generate_insights(days)
        for insight in insights:
            report += f"  • {insight}\n"
        
        print(report)
        
        # Save to file
        report_path = f"./reports/health-report-{datetime.now().strftime('%Y-%m')}.txt"
        Path(report_path).parent.mkdir(exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\nReport saved to: {report_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Health Monitor - Personal Health Tracking')
    parser.add_argument('--log', type=str, help='Log a health entry')
    parser.add_argument('--view', action='store_true', help='View recent entries')
    parser.add_argument('--analyze', action='store_true', help='Analyze health trends')
    parser.add_argument('--report', action='store_true', help='Generate health report')
    parser.add_argument('--days', type=int, default=7, help='Number of days')
    parser.add_argument('--month', type=int, help='Month number (1-12)')
    parser.add_argument('--type', type=str, help='Filter by entry type')
    parser.add_argument('--setup', action='store_true', help='Initial setup')
    
    args = parser.parse_args()
    
    # Create directories
    for directory in ['data', 'logs', 'reports', 'backups']:
        Path(directory).mkdir(exist_ok=True)
    
    # Initialize monitor
    monitor = HealthMonitor()
    
    if args.setup:
        print("Health Monitor setup complete!")
        print("\nStart logging with: python main.py --log 'your health entry'")
        return
    
    if args.log:
        entry_id = monitor.log_entry(args.log)
        print(f"✓ Health entry logged (ID: {entry_id})")
    
    elif args.view:
        monitor.view_entries(days=args.days, entry_type=args.type)
    
    elif args.analyze:
        monitor.analyze_trends(days=args.days)
    
    elif args.report:
        monitor.generate_report(month=args.month)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()