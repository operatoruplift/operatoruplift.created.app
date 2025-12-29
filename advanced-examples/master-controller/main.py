#!/usr/bin/env python3
"""
Master Controller - Agent Orchestration System

Central coordination system for managing multiple UPLIFT agents.

Usage:
    python main.py --start
    python main.py --list
    python main.py --agent-start code-auditor
"""

import os
import sys
import yaml
import json
import logging
import argparse
import sqlite3
import subprocess
import threading
import time
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from queue import PriorityQueue, Queue
from enum import Enum
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/master-controller.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('master-controller')


class AgentStatus(Enum):
    """Agent status enum"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    UNKNOWN = "unknown"


class TaskStatus(Enum):
    """Task status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentInfo:
    """Agent information"""
    name: str
    manifest_path: str
    status: AgentStatus
    pid: Optional[int] = None
    priority: int = 5
    last_health_check: Optional[str] = None
    restart_count: int = 0
    resource_usage: Dict[str, Any] = None


@dataclass
class Task:
    """Task information"""
    id: str
    agent: str
    action: str
    params: Dict[str, Any]
    priority: int
    status: TaskStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Any = None
    error: Optional[str] = None


class MessageBus:
    """Simple in-memory message bus"""
    
    def __init__(self):
        self.subscribers = {}
        self.messages = Queue(maxsize=1000)
        self.running = False
        self.thread = None
    
    def start(self):
        """Start message bus"""
        self.running = True
        self.thread = threading.Thread(target=self._process_messages, daemon=True)
        self.thread.start()
        logger.info("Message bus started")
    
    def stop(self):
        """Stop message bus"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Message bus stopped")
    
    def publish(self, topic: str, message: Dict[str, Any]):
        """Publish message to topic"""
        self.messages.put((topic, message))
    
    def subscribe(self, topic: str, callback):
        """Subscribe to topic"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
    
    def _process_messages(self):
        """Process messages in background"""
        while self.running:
            try:
                if not self.messages.empty():
                    topic, message = self.messages.get(timeout=1)
                    if topic in self.subscribers:
                        for callback in self.subscribers[topic]:
                            try:
                                callback(message)
                            except Exception as e:
                                logger.error(f"Error in subscriber callback: {e}")
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing messages: {e}")


class ResourceMonitor:
    """Monitors system resources"""
    
    def __init__(self):
        self.process_cache = {}
    
    def get_agent_resources(self, pid: int) -> Dict[str, Any]:
        """Get resource usage for agent process"""
        try:
            if pid in self.process_cache:
                process = self.process_cache[pid]
            else:
                process = psutil.Process(pid)
                self.process_cache[pid] = process
            
            return {
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_mb': process.memory_info().rss / (1024 * 1024),
                'memory_percent': process.memory_percent(),
                'num_threads': process.num_threads(),
                'status': process.status()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            if pid in self.process_cache:
                del self.process_cache[pid]
            return None
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get overall system resources"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
        }


class MasterController:
    """Main master controller class"""
    
    def __init__(self, config_path: str = "agent.yaml"):
        self.config = self._load_config(config_path)
        self.agents: Dict[str, AgentInfo] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue = PriorityQueue()
        self.message_bus = MessageBus()
        self.resource_monitor = ResourceMonitor()
        self.running = False
        self.threads = []
        
        # Initialize database
        self._init_database()
        
        logger.info("Master Controller initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _init_database(self):
        """Initialize database"""
        db_path = self.config.get('settings', {}).get('database', {}).get('path', './data/master.db')
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                name TEXT PRIMARY KEY,
                manifest_path TEXT,
                status TEXT,
                pid INTEGER,
                last_seen DATETIME,
                restart_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                agent TEXT,
                action TEXT,
                params TEXT,
                priority INTEGER,
                status TEXT,
                created_at DATETIME,
                started_at DATETIME,
                completed_at DATETIME,
                result TEXT,
                error TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                type TEXT,
                source TEXT,
                data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def discover_agents(self):
        """Discover agents in agent directory"""
        agent_dir = self.config.get('settings', {}).get('agents', {}).get('directory', './agents')
        
        if not os.path.exists(agent_dir):
            logger.warning(f"Agent directory not found: {agent_dir}")
            return
        
        for agent_name in os.listdir(agent_dir):
            agent_path = os.path.join(agent_dir, agent_name)
            manifest_path = os.path.join(agent_path, 'manifest.yaml')
            
            if os.path.isdir(agent_path) and os.path.exists(manifest_path):
                self.register_agent(agent_name, manifest_path)
        
        logger.info(f"Discovered {len(self.agents)} agents")
    
    def register_agent(self, name: str, manifest_path: str):
        """Register an agent"""
        try:
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
            
            agent = AgentInfo(
                name=name,
                manifest_path=manifest_path,
                status=AgentStatus.STOPPED,
                priority=manifest.get('priority', 5)
            )
            
            self.agents[name] = agent
            logger.info(f"Registered agent: {name}")
        
        except Exception as e:
            logger.error(f"Error registering agent {name}: {e}")
    
    def start_agent(self, name: str) -> bool:
        """Start an agent"""
        if name not in self.agents:
            logger.error(f"Agent not found: {name}")
            return False
        
        agent = self.agents[name]
        
        if agent.status == AgentStatus.RUNNING:
            logger.warning(f"Agent already running: {name}")
            return True
        
        try:
            agent.status = AgentStatus.STARTING
            
            # Get agent directory
            agent_dir = os.path.dirname(agent.manifest_path)
            main_script = os.path.join(agent_dir, 'main.py')
            
            if not os.path.exists(main_script):
                logger.error(f"Agent main script not found: {main_script}")
                agent.status = AgentStatus.FAILED
                return False
            
            # Start agent process
            process = subprocess.Popen(
                [sys.executable, main_script],
                cwd=agent_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            agent.pid = process.pid
            agent.status = AgentStatus.RUNNING
            agent.last_health_check = datetime.now().isoformat()
            
            logger.info(f"Started agent: {name} (PID: {agent.pid})")
            self.message_bus.publish('agent.status', {
                'agent': name,
                'status': 'started',
                'pid': agent.pid
            })
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting agent {name}: {e}")
            agent.status = AgentStatus.FAILED
            return False
    
    def stop_agent(self, name: str) -> bool:
        """Stop an agent"""
        if name not in self.agents:
            logger.error(f"Agent not found: {name}")
            return False
        
        agent = self.agents[name]
        
        if agent.status != AgentStatus.RUNNING or not agent.pid:
            logger.warning(f"Agent not running: {name}")
            return True
        
        try:
            agent.status = AgentStatus.STOPPING
            
            # Try graceful shutdown
            process = psutil.Process(agent.pid)
            process.terminate()
            
            # Wait for process to stop
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                # Force kill
                process.kill()
            
            agent.status = AgentStatus.STOPPED
            agent.pid = None
            
            logger.info(f"Stopped agent: {name}")
            self.message_bus.publish('agent.status', {
                'agent': name,
                'status': 'stopped'
            })
            
            return True
        
        except Exception as e:
            logger.error(f"Error stopping agent {name}: {e}")
            return False
    
    def submit_task(self, agent: str, action: str, params: Dict[str, Any], priority: int = 5) -> str:
        """Submit a task to the queue"""
        task_id = f"{agent}_{action}_{int(time.time()*1000)}"
        
        task = Task(
            id=task_id,
            agent=agent,
            action=action,
            params=params,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now().isoformat()
        )
        
        self.tasks[task_id] = task
        self.task_queue.put((-priority, task_id))  # Negative for max heap
        
        logger.info(f"Task submitted: {task_id} (priority: {priority})")
        return task_id
    
    def health_check_loop(self):
        """Periodic health checks for agents"""
        while self.running:
            try:
                for name, agent in self.agents.items():
                    if agent.status == AgentStatus.RUNNING and agent.pid:
                        resources = self.resource_monitor.get_agent_resources(agent.pid)
                        
                        if resources is None:
                            # Process died
                            logger.warning(f"Agent {name} is not running")
                            agent.status = AgentStatus.FAILED
                            
                            # Try to restart
                            if self.config.get('settings', {}).get('agents', {}).get('restart_on_failure', True):
                                max_attempts = self.config.get('settings', {}).get('agents', {}).get('max_restart_attempts', 3)
                                if agent.restart_count < max_attempts:
                                    agent.restart_count += 1
                                    logger.info(f"Restarting agent {name} (attempt {agent.restart_count}/{max_attempts})")
                                    self.start_agent(name)
                        else:
                            agent.resource_usage = resources
                            agent.last_health_check = datetime.now().isoformat()
                
                time.sleep(60)  # Check every minute
            
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                time.sleep(60)
    
    def start(self):
        """Start the master controller"""
        logger.info("Starting Master Controller")
        self.running = True
        
        # Start message bus
        self.message_bus.start()
        
        # Discover and optionally start agents
        if self.config.get('settings', {}).get('agents', {}).get('auto_discover', True):
            self.discover_agents()
        
        if self.config.get('settings', {}).get('agents', {}).get('auto_start', False):
            for name in self.agents:
                self.start_agent(name)
        
        # Start health check thread
        health_thread = threading.Thread(target=self.health_check_loop, daemon=True)
        health_thread.start()
        self.threads.append(health_thread)
        
        logger.info("Master Controller started")
    
    def stop(self):
        """Stop the master controller"""
        logger.info("Stopping Master Controller")
        self.running = False
        
        # Stop all agents
        for name in list(self.agents.keys()):
            self.stop_agent(name)
        
        # Stop message bus
        self.message_bus.stop()
        
        # Wait for threads
        for thread in self.threads:
            thread.join(timeout=5)
        
        logger.info("Master Controller stopped")
    
    def list_agents(self):
        """List all agents"""
        print(f"\n{'='*80}")
        print("Registered Agents")
        print(f"{'='*80}\n")
        
        for name, agent in self.agents.items():
            status_symbol = {
                AgentStatus.RUNNING: "✓",
                AgentStatus.STOPPED: "●",
                AgentStatus.FAILED: "✗"
            }.get(agent.status, "?")
            
            print(f"{status_symbol} {name:20} Status: {agent.status.value:10} ", end="")
            if agent.pid:
                print(f"PID: {agent.pid:6} ", end="")
            if agent.resource_usage:
                print(f"CPU: {agent.resource_usage['cpu_percent']:.1f}% ", end="")
                print(f"Mem: {agent.resource_usage['memory_mb']:.0f}MB", end="")
            print()
        
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Master Controller - Agent Orchestration')
    parser.add_argument('--init', action='store_true', help='Initialize master controller')
    parser.add_argument('--start', action='store_true', help='Start master controller')
    parser.add_argument('--stop', action='store_true', help='Stop master controller')
    parser.add_argument('--list', action='store_true', help='List agents')
    parser.add_argument('--agent-start', type=str, help='Start specific agent')
    parser.add_argument('--agent-stop', type=str, help='Stop specific agent')
    parser.add_argument('--config', type=str, default='agent.yaml', help='Config file')
    parser.add_argument('--foreground', action='store_true', help='Run in foreground')
    
    args = parser.parse_args()
    
    # Create directories
    for directory in ['logs', 'data', 'agents', 'config']:
        Path(directory).mkdir(exist_ok=True)
    
    # Initialize controller
    controller = MasterController(args.config)
    
    if args.init:
        print("Master Controller initialized")
        print("\nNext steps:")
        print("  1. Place agent directories in ./agents/")
        print("  2. Run: python main.py --start")
        return
    
    if args.start:
        controller.start()
        
        if args.foreground:
            # Run in foreground
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                controller.stop()
        else:
            print("Master Controller started in background")
    
    elif args.list:
        controller.discover_agents()
        controller.list_agents()
    
    elif args.agent_start:
        controller.discover_agents()
        if controller.start_agent(args.agent_start):
            print(f"Agent {args.agent_start} started")
        else:
            print(f"Failed to start agent {args.agent_start}")
    
    elif args.agent_stop:
        controller.discover_agents()
        if controller.stop_agent(args.agent_stop):
            print(f"Agent {args.agent_stop} stopped")
        else:
            print(f"Failed to stop agent {args.agent_stop}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()