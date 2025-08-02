#!/usr/bin/env python3
"""
Simple Agent Log Analyzer

Analyzes agent execution logs to provide insights into performance and errors.
"""

import re
import os
from collections import Counter
from datetime import datetime

def analyze_agent_logs(log_file="agent.log"):
    """Analyze agent logs and generate a report."""
    
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = f.readlines()
    except UnicodeDecodeError:
        with open(log_file, 'r', encoding='latin-1') as f:
            logs = f.readlines()
    
    # Initialize counters
    execution_count = 0
    error_count = 0
    tool_usage = Counter()
    error_types = Counter()
    
    # Analyze logs
    for line in logs:
        line = line.strip()
        
        # Count executions
        if 'Starting LangGraph execution' in line:
            execution_count += 1
        
        # Count errors
        if 'ERROR' in line:
            error_count += 1
            
            # Categorize errors
            if 'LLM response has no candidates' in line:
                error_types['llm_no_candidates'] += 1
            elif 'Recursion limit' in line:
                error_types['recursion_limit'] += 1
            elif 'coroutine object' in line:
                error_types['async_error'] += 1
            elif 'JSONDecodeError' in line:
                error_types['json_parse_error'] += 1
            else:
                error_types['other'] += 1
        
        # Count tool usage
        if 'Action: Executing' in line:
            match = re.search(r'Action: Executing (\w+)', line)
            if match:
                tool_usage[match.group(1)] += 1
    
    # Generate report
    print("=" * 50)
    print("AGENT LOG ANALYSIS REPORT")
    print("=" * 50)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Log file: {log_file}")
    print(f"Total log lines: {len(logs)}")
    print()
    
    print("EXECUTION STATISTICS")
    print("-" * 20)
    print(f"Total executions: {execution_count}")
    print(f"Total errors: {error_count}")
    print(f"Success rate: {((execution_count - error_count) / execution_count * 100):.1f}%" if execution_count > 0 else "N/A")
    print()
    
    print("TOOL USAGE")
    print("-" * 20)
    for tool, count in tool_usage.most_common():
        print(f"{tool}: {count} calls")
    print()
    
    print("ERROR ANALYSIS")
    print("-" * 20)
    for error_type, count in error_types.most_common():
        print(f"{error_type}: {count}")
    print()
    
    print("RECOMMENDATIONS")
    print("-" * 20)
    if error_types['recursion_limit'] > 0:
        print("⚠️  Consider reducing loop limits or improving loop detection")
    if error_types['llm_no_candidates'] > 0:
        print("⚠️  LLM response issues detected - check message formatting")
    if error_types['async_error'] > 0:
        print("⚠️  Async/await issues detected - check event loop handling")
    if error_count == 0:
        print("✅ No errors detected - agent running smoothly!")
    
    print("=" * 50)

if __name__ == "__main__":
    analyze_agent_logs() 