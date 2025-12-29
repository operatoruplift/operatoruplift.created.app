#!/usr/bin/env python3
"""
Kill Switch - Emergency Agent Shutdown

Provides emergency stop functionality for UPLIFT agents.

Usage:
    python kill_switch.py --emergency-stop
    python kill_switch.py --graceful-shutdown
"""

import os
import sys
import signal
import psutil
import logging
import argparse
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kill-switch')


class KillSwitch:
    """Emergency kill switch for agents"""
    
    def __init__(self):
        self.stopped_processes = []
    
    def find_agent_processes(self):
        """Find all running agent processes"""
        agent_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('agent' in arg.lower() or 'main.py' in arg for arg in cmdline):
                    agent_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return agent_processes
    
    def emergency_stop(self):
        """Emergency stop all agents"""
        logger.warning("EMERGENCY STOP INITIATED")
        
        processes = self.find_agent_processes()
        logger.info(f"Found {len(processes)} agent processes")
        
        for proc in processes:
            try:
                logger.warning(f"Killing process {proc.pid}: {proc.name()}")
                proc.kill()
                self.stopped_processes.append(proc.pid)
            except Exception as e:
                logger.error(f"Error killing process {proc.pid}: {e}")
        
        logger.warning(f"Emergency stop complete. Stopped {len(self.stopped_processes)} processes")
        
        # Log to file
        self._log_emergency_stop()
    
    def graceful_shutdown(self, timeout=30):
        """Gracefully shutdown all agents"""
        logger.info("Graceful shutdown initiated")
        
        processes = self.find_agent_processes()
        logger.info(f"Found {len(processes)} agent processes")
        
        for proc in processes:
            try:
                logger.info(f"Sending SIGTERM to {proc.pid}: {proc.name()}")
                proc.terminate()
            except Exception as e:
                logger.error(f"Error terminating process {proc.pid}: {e}")
        
        # Wait for processes to stop
        import time
        time.sleep(timeout)
        
        # Force kill remaining
        for proc in processes:
            try:
                if proc.is_running():
                    logger.warning(f"Force killing {proc.pid}")
                    proc.kill()
            except Exception as e:
                pass
        
        logger.info("Graceful shutdown complete")
    
    def stop_agent(self, agent_name: str):
        """Stop specific agent"""
        logger.info(f"Stopping agent: {agent_name}")
        
        processes = self.find_agent_processes()
        stopped = False
        
        for proc in processes:
            try:
                cmdline = ' '.join(proc.cmdline())
                if agent_name in cmdline:
                    logger.info(f"Stopping process {proc.pid}")
                    proc.terminate()
                    stopped = True
            except Exception as e:
                logger.error(f"Error stopping process: {e}")
        
        if not stopped:
            logger.warning(f"Agent not found: {agent_name}")
    
    def _log_emergency_stop(self):
        """Log emergency stop event"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"emergency-stop-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
        
        with open(log_file, 'w') as f:
            f.write(f"Emergency Stop Event\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Stopped Processes: {len(self.stopped_processes)}\n")
            f.write(f"PIDs: {', '.join(map(str, self.stopped_processes))}\n")


def main():
    parser = argparse.ArgumentParser(description='Kill Switch - Emergency Agent Shutdown')
    parser.add_argument('--emergency-stop', action='store_true', help='Emergency stop all agents')
    parser.add_argument('--graceful-shutdown', action='store_true', help='Graceful shutdown')
    parser.add_argument('--stop-agent', type=str, help='Stop specific agent')
    parser.add_argument('--list', action='store_true', help='List running agents')
    
    args = parser.parse_args()
    
    kill_switch = KillSwitch()
    
    if args.emergency_stop:
        confirm = input("Are you sure you want to emergency stop all agents? (yes/no): ")
        if confirm.lower() == 'yes':
            kill_switch.emergency_stop()
        else:
            print("Cancelled")
    
    elif args.graceful_shutdown:
        kill_switch.graceful_shutdown()
    
    elif args.stop_agent:
        kill_switch.stop_agent(args.stop_agent)
    
    elif args.list:
        processes = kill_switch.find_agent_processes()
        print(f"\nRunning Agents: {len(processes)}\n")
        for proc in processes:
            try:
                print(f"PID {proc.pid}: {' '.join(proc.cmdline())}")
            except:
                pass
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()