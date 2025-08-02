#!/usr/bin/env python3
"""
Agent Log Analysis Tool

This script analyzes agent execution logs to provide insights into:
- Execution patterns
- Tool usage statistics
- Performance metrics
- Error analysis
- State transitions
"""

import json
import re
import os
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import pandas as pd

class AgentLogAnalyzer:
    """Analyzes agent execution logs for insights and performance metrics."""
    
    def __init__(self, log_file_path: str = "agent.log"):
        self.log_file_path = log_file_path
        self.logs = []
        self.analysis_results = {}
        
    def load_logs(self) -> bool:
        """Load and parse agent logs."""
        if not os.path.exists(self.log_file_path):
            print(f"Log file not found: {self.log_file_path}")
            return False
            
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.logs.append(line)
            print(f"Loaded {len(self.logs)} log entries")
            return True
        except Exception as e:
            print(f"Error loading logs: {e}")
            return False
    
    def parse_log_entry(self, log_line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log entry."""
        # Pattern to match log entries
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - (.+)'
        match = re.match(pattern, log_line)
        
        if match:
            timestamp, logger_name, level, message = match.groups()
            return {
                'timestamp': timestamp,
                'logger': logger_name,
                'level': level,
                'message': message,
                'datetime': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S,%f')
            }
        return None
    
    def analyze_execution_patterns(self) -> Dict[str, Any]:
        """Analyze execution patterns and flow."""
        parsed_logs = [self.parse_log_entry(log) for log in self.logs if self.parse_log_entry(log)]
        
        # Filter for notion_agent logs
        agent_logs = [log for log in parsed_logs if log['logger'] == 'notion_agent']
        
        # Analyze node transitions
        node_transitions = []
        current_node = None
        
        for log in agent_logs:
            message = log['message']
            if 'Perception: Gathering context' in message:
                current_node = 'perception'
            elif 'Reasoning: Determining next action' in message:
                if current_node:
                    node_transitions.append((current_node, 'reasoning'))
                current_node = 'reasoning'
            elif 'Action: Executing' in message:
                if current_node:
                    node_transitions.append((current_node, 'action'))
                current_node = 'action'
        
        # Count transitions
        transition_counts = Counter(node_transitions)
        
        return {
            'total_executions': len([log for log in agent_logs if 'Starting LangGraph execution' in log['message']]),
            'node_transitions': dict(transition_counts),
            'execution_flows': self._extract_execution_flows(agent_logs)
        }
    
    def _extract_execution_flows(self, agent_logs: List[Dict[str, Any]]) -> List[List[str]]:
        """Extract complete execution flows."""
        flows = []
        current_flow = []
        
        for log in agent_logs:
            message = log['message']
            
            if 'Starting LangGraph execution' in message:
                if current_flow:
                    flows.append(current_flow)
                current_flow = ['start']
            elif 'Perception: Gathering context' in message:
                current_flow.append('perception')
            elif 'Reasoning: Determining next action' in message:
                current_flow.append('reasoning')
            elif 'Action: Executing' in message:
                # Extract action name
                action_match = re.search(r'Action: Executing (\w+)', message)
                if action_match:
                    current_flow.append(f"action_{action_match.group(1)}")
                else:
                    current_flow.append('action')
            elif 'Agent ending' in message or 'Error in LangGraph execution' in message:
                current_flow.append('end')
                flows.append(current_flow)
                current_flow = []
        
        if current_flow:
            flows.append(current_flow)
        
        return flows
    
    def analyze_tool_usage(self) -> Dict[str, Any]:
        """Analyze tool usage patterns."""
        tool_usage = defaultdict(int)
        tool_errors = defaultdict(int)
        
        for log in self.logs:
            # Count tool executions
            if 'Action: Executing' in log:
                action_match = re.search(r'Action: Executing (\w+)', log)
                if action_match:
                    tool_name = action_match.group(1)
                    tool_usage[tool_name] += 1
            
            # Count tool errors
            if 'ERROR' in log and any(tool in log for tool in ['search_tasks', 'get_routines', 'create_task', 'update_task', 'send_notification']):
                for tool in ['search_tasks', 'get_routines', 'create_task', 'update_task', 'send_notification']:
                    if tool in log:
                        tool_errors[tool] += 1
        
        return {
            'tool_usage': dict(tool_usage),
            'tool_errors': dict(tool_errors),
            'success_rate': self._calculate_success_rate(tool_usage, tool_errors)
        }
    
    def _calculate_success_rate(self, usage: Dict[str, int], errors: Dict[str, int]) -> Dict[str, float]:
        """Calculate success rate for each tool."""
        success_rates = {}
        for tool, count in usage.items():
            error_count = errors.get(tool, 0)
            success_rates[tool] = ((count - error_count) / count * 100) if count > 0 else 0
        return success_rates
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics."""
        parsed_logs = [self.parse_log_entry(log) for log in self.logs if self.parse_log_entry(log)]
        agent_logs = [log for log in parsed_logs if log['logger'] == 'notion_agent']
        
        # Calculate execution times
        execution_times = []
        start_time = None
        
        for log in agent_logs:
            if 'Starting LangGraph execution' in log['message']:
                start_time = log['datetime']
            elif ('Agent ending' in log['message'] or 'Error in LangGraph execution' in log['message']) and start_time:
                end_time = log['datetime']
                execution_time = (end_time - start_time).total_seconds()
                execution_times.append(execution_time)
                start_time = None
        
        # Calculate loop counts
        loop_counts = []
        for log in agent_logs:
            if 'loop_count' in log['message']:
                match = re.search(r'loop_count.*?(\d+)', log['message'])
                if match:
                    loop_counts.append(int(match.group(1)))
        
        return {
            'total_executions': len(execution_times),
            'avg_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0,
            'min_execution_time': min(execution_times) if execution_times else 0,
            'max_execution_time': max(execution_times) if execution_times else 0,
            'avg_loop_count': sum(loop_counts) / len(loop_counts) if loop_counts else 0,
            'max_loop_count': max(loop_counts) if loop_counts else 0
        }
    
    def analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns."""
        errors = []
        error_types = Counter()
        
        for log in self.logs:
            if 'ERROR' in log:
                errors.append(log)
                # Categorize errors
                if 'LLM response has no candidates' in log:
                    error_types['llm_no_candidates'] += 1
                elif 'Recursion limit' in log:
                    error_types['recursion_limit'] += 1
                elif 'coroutine object' in log:
                    error_types['async_error'] += 1
                elif 'JSONDecodeError' in log:
                    error_types['json_parse_error'] += 1
                else:
                    error_types['other'] += 1
        
        return {
            'total_errors': len(errors),
            'error_types': dict(error_types),
            'recent_errors': errors[-10:] if errors else []  # Last 10 errors
        }
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        if not self.load_logs():
            return "Failed to load logs"
        
        # Run all analyses
        execution_patterns = self.analyze_execution_patterns()
        tool_usage = self.analyze_tool_usage()
        performance = self.analyze_performance()
        errors = self.analyze_errors()
        
        # Generate report
        report = []
        report.append("=" * 60)
        report.append("AGENT LOG ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Log file: {self.log_file_path}")
        report.append(f"Total log entries: {len(self.logs)}")
        report.append("")
        
        # Execution Patterns
        report.append("EXECUTION PATTERNS")
        report.append("-" * 20)
        report.append(f"Total executions: {execution_patterns['total_executions']}")
        report.append("Node transitions:")
        for (from_node, to_node), count in execution_patterns['node_transitions'].items():
            report.append(f"  {from_node} → {to_node}: {count}")
        report.append("")
        
        # Tool Usage
        report.append("TOOL USAGE")
        report.append("-" * 20)
        for tool, count in tool_usage['tool_usage'].items():
            success_rate = tool_usage['success_rate'].get(tool, 0)
            report.append(f"{tool}: {count} calls ({success_rate:.1f}% success)")
        report.append("")
        
        # Performance
        report.append("PERFORMANCE METRICS")
        report.append("-" * 20)
        report.append(f"Average execution time: {performance['avg_execution_time']:.2f}s")
        report.append(f"Min execution time: {performance['min_execution_time']:.2f}s")
        report.append(f"Max execution time: {performance['max_execution_time']:.2f}s")
        report.append(f"Average loop count: {performance['avg_loop_count']:.1f}")
        report.append(f"Max loop count: {performance['max_loop_count']}")
        report.append("")
        
        # Errors
        report.append("ERROR ANALYSIS")
        report.append("-" * 20)
        report.append(f"Total errors: {errors['total_errors']}")
        for error_type, count in errors['error_types'].items():
            report.append(f"{error_type}: {count}")
        report.append("")
        
        # Recent errors
        if errors['recent_errors']:
            report.append("RECENT ERRORS (Last 5)")
            report.append("-" * 20)
            for error in errors['recent_errors'][-5:]:
                report.append(f"  {error}")
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 20)
        
        if errors['error_types'].get('recursion_limit', 0) > 0:
            report.append("⚠️  Consider reducing loop limits or improving loop detection")
        
        if errors['error_types'].get('llm_no_candidates', 0) > 0:
            report.append("⚠️  LLM response issues detected - check message formatting")
        
        if performance['avg_loop_count'] > 3:
            report.append("⚠️  High loop counts detected - consider optimizing agent logic")
        
        if tool_usage['success_rate']:
            low_success_tools = [tool for tool, rate in tool_usage['success_rate'].items() if rate < 80]
            if low_success_tools:
                report.append(f"⚠️  Low success rate for tools: {', '.join(low_success_tools)}")
        
        report.append("✅ Agent analysis complete")
        
        return "\n".join(report)
    
    def save_analysis(self, output_file: str = "agent_analysis_report.txt"):
        """Save analysis report to file."""
        report = self.generate_report()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Analysis report saved to: {output_file}")

def main():
    """Main function to run the analysis."""
    print("Agent Log Analyzer")
    print("=" * 40)
    
    # Check for log files
    log_files = ["agent.log", "logs/agent.log"]
    log_file = None
    
    for file_path in log_files:
        if os.path.exists(file_path):
            log_file = file_path
            break
    
    if not log_file:
        print("No log files found. Please ensure agent.log exists.")
        return
    
    # Create analyzer and run analysis
    analyzer = AgentLogAnalyzer(log_file)
    
    # Generate and display report
    report = analyzer.generate_report()
    print(report)
    
    # Save report
    analyzer.save_analysis()
    
    print("\nAnalysis complete! Check agent_analysis_report.txt for detailed results.")

if __name__ == "__main__":
    main() 