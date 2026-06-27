#!/usr/bin/env python3
"""
Meridian Screening Tracker
Tracks all screening decisions from Meridian logs.
Parses PM2 stdout logs AND agent log files and records:
- All candidates found
- Which ones passed/failed filters
- Reason for rejection
- Deploy decisions

Usage:
  python3 meridian_screening_tracker.py --parse    # Parse latest logs
  python3 meridian_screening_tracker.py --analyze   # Analyze collected data
  python3 meridian_screening_tracker.py --report    # Generate report

PITFALL: Meridian's screening data lives in PM2 stdout (~/.pm2/logs/meridian-out-0.log),
NOT in the agent log directory. The --parse command checks both locations.

PITFALL: PM2 log rotation — after `pm2 delete && pm2 start`, PM2 increments log file number
(meridian-out-0.log → meridian-out-2.log). This script hardcodes meridian-out-0.log.
Check `pm2 show meridian` → 'out log path' after restarts.
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

LOGS_DIR = Path.home() / "mona-workspace" / "meridian" / "logs"
PM2_LOG = Path.home() / ".pm2" / "logs" / "meridian-out-0.log"
DATA_DIR = Path.home() / "mona-workspace" / "meridian" / "screening_data"
DATA_DIR.mkdir(exist_ok=True)

TRACKER_FILE = DATA_DIR / "screening_tracker.json"
ANALYSIS_FILE = DATA_DIR / "analysis.json"

def load_tracker():
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE) as f:
            return json.load(f)
    return {"cycles": [], "candidates": [], "stats": {}}

def save_tracker(data):
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def parse_log_file(log_path):
    """Parse a Meridian PM2 log file for screening decisions.
    
    Supports both agent log format and PM2 stdout format.
    PM2 format: [2026-06-08T09:35:07.497Z] [SCREENING] ...
    
    Key patterns:
    - Cycle start: [CRON] Starting screening cycle [model: ...]
    - Bot filter: [SCREENING] Bot-holder filter: dropped X — bots Y% > Z%
    - Safety block: [SAFETY_BLOCK] deploy_position blocked: reason
    - Deploy: [deploy_position] ✓ X SOL (Yms)
    - Best candidate: BEST LOOKING CANDIDATE
    - Cycle end: Cycle finished with no valid entry.
    """
    if not log_path.exists():
        return []
    
    cycles = []
    current_cycle = None
    candidates_this_cycle = []
    deploy_this_cycle = None
    best_candidate = None
    reject_reason = None
    
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            
            # Detect screening cycle start (PM2 or agent format)
            if '[CRON] Starting screening cycle' in line:
                # Save previous cycle
                if current_cycle:
                    current_cycle['candidates'] = candidates_this_cycle
                    current_cycle['deploy'] = deploy_this_cycle
                    current_cycle['best_candidate'] = best_candidate
                    current_cycle['reject_reason'] = reject_reason
                    cycles.append(current_cycle)
                
                ts_match = re.search(r'\[(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\]', line)
                timestamp = ts_match.group(1) if ts_match else line.split(']')[0].strip('[')
                current_cycle = {
                    "timestamp": timestamp,
                    "candidates": [],
                    "deploy": None,
                    "reject_reason": None,
                    "best_candidate": None
                }
                candidates_this_cycle = []
                deploy_this_cycle = None
                best_candidate = None
                reject_reason = None
            
            if not current_cycle:
                continue
            
            # Bot-holder filter (PM2 format: [SCREENING] Bot-holder filter: dropped X — bots Y% > Z%)
            if '[SCREENING] Bot-holder filter:' in line:
                match = re.search(r'dropped (\S+) — bots (\d+\.?\d*)% > (\d+)%', line)
                if match:
                    candidates_this_cycle.append({
                        "pool": match.group(1),
                        "bot_pct": float(match.group(2)),
                        "max_bot_pct": int(match.group(3)),
                        "rejected_by": "bot_filter",
                        "timestamp": current_cycle["timestamp"]
                    })
            
            # Safety block (PM2 format: [SAFETY_BLOCK] deploy_position blocked: ...)
            if '[SAFETY_BLOCK]' in line:
                match = re.search(r'deploy_position blocked: (.+)', line)
                if match:
                    reason = match.group(1)
                    entry = {
                        "pool": "unknown",
                        "reason": reason,
                        "rejected_by": "safety_block",
                        "timestamp": current_cycle["timestamp"]
                    }
                    fee_match = re.search(r'fee/active-TVL (\d+\.?\d*)%.*minFeeActiveTvlRatio (\d+\.?\d*)%', reason)
                    if fee_match:
                        entry["fee_tvl_actual"] = float(fee_match.group(1))
                        entry["fee_tvl_threshold"] = float(fee_match.group(2))
                    candidates_this_cycle.append(entry)
            
            # Successful deploy (PM2 format: [deploy_position] ✓ POOLNAME X.X SOL)
            if '[deploy_position]' in line and '✓' in line:
                match = re.search(r'✓ (\S+) (\d+\.?\d*) SOL', line)
                if match:
                    deploy_this_cycle = {
                        "pool": match.group(1),
                        "amount": float(match.group(2)),
                        "timestamp": current_cycle["timestamp"]
                    }
            
            # Best candidate
            if 'BEST LOOKING CANDIDATE' in line:
                best_candidate = line.split('BEST LOOKING CANDIDATE')[-1].strip()
            
            # WHY SKIPPED
            if 'WHY SKIPPED' in line:
                reject_reason = line.split('WHY SKIPPED')[-1].strip()
            
            # Cycle end markers
            if 'Cycle finished with no valid entry' in line or ('REJECTED' in line and 'NO DEPLOY' in line):
                if current_cycle:
                    current_cycle['candidates'] = candidates_this_cycle
                    current_cycle['deploy'] = deploy_this_cycle
                    current_cycle['best_candidate'] = best_candidate
                    current_cycle['reject_reason'] = reject_reason
                    cycles.append(current_cycle)
                    current_cycle = None
                    candidates_this_cycle = []
                    deploy_this_cycle = None
    
    # Don't forget the last cycle if log didn't end with a marker
    if current_cycle:
        current_cycle['candidates'] = candidates_this_cycle
        current_cycle['deploy'] = deploy_this_cycle
        current_cycle['best_candidate'] = best_candidate
        current_cycle['reject_reason'] = reject_reason
        cycles.append(current_cycle)
    
    return cycles

def analyze_data(tracker):
    if not tracker["cycles"]:
        return {"insufficient_data": True}
    
    # Load actual config values for accurate recommendations
    config_file = Path.home() / "mona-workspace" / "meridian" / "user-config.json"
    config = {}
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
    
    cycles = tracker["cycles"]
    candidates = tracker["candidates"]
    
    rejection_counts = {}
    for c in candidates:
        reason = c.get("rejected_by", "unknown")
        rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
    
    deploy_cycles = [c for c in cycles if c.get("deploy")]
    no_deploy_cycles = [c for c in cycles if not c.get("deploy")]
    
    bot_pcts = [c.get("bot_pct", 0) for c in candidates if "bot_pct" in c]
    avg_bot_pct = sum(bot_pcts) / len(bot_pcts) if bot_pcts else 0
    
    fee_tvl_ratios = []
    for c in candidates:
        if c.get("rejected_by") == "safety_block" and "fee/active-TVL" in c.get("reason", ""):
            match = re.search(r"(\d+\.?\d*)%", c["reason"])
            if match:
                fee_tvl_ratios.append(float(match.group(1)))
    avg_fee_tvl = sum(fee_tvl_ratios) / len(fee_tvl_ratios) if fee_tvl_ratios else 0
    
    current_bot_pct = config.get("maxBotHoldersPct", 25)
    current_fee_tvl = config.get("minFeeActiveTvlRatio", 0.03)
    
    analysis = {
        "total_cycles": len(cycles),
        "total_candidates": len(candidates),
        "deploy_cycles": len(deploy_cycles),
        "no_deploy_cycles": len(no_deploy_cycles),
        "deploy_rate": len(deploy_cycles) / len(cycles) if cycles else 0,
        "rejection_counts": rejection_counts,
        "avg_bot_pct": round(avg_bot_pct, 2),
        "avg_fee_tvl_rejected": round(avg_fee_tvl, 4),
        "recommendations": []
    }
    
    # Generate recommendations based on actual config
    # BUG FIX (Jun10): old cap was 35 which LOWERED threshold when current > 35 (e.g., 40→35).
    # Fixed to cap at 55 — always raises or stays same, never makes bot filter stricter.
    if rejection_counts.get("bot_filter", 0) > 3:
        suggested = min(current_bot_pct + 5, 55)  # bump by 5, cap at 55
        analysis["recommendations"].append({
            "parameter": "maxBotHoldersPct",
            "current": current_bot_pct,
            "suggested": suggested,
            "reason": f"Bot filter rejecting {rejection_counts['bot_filter']} candidates — consider raising threshold from {current_bot_pct}% to {suggested}%"
        })
    
    # BUG FIX (Jun10): old logic max(current - 0.01, 0.01) with current=0.005 gave 0.01 (HIGHER),
    # but wording said "lowering". Fixed: proportional reduction (40% decrease, floor 0.001).
    # When safety_block rejections are high, the threshold is too strict — lower it.
    if rejection_counts.get("safety_block", 0) > 2:
        suggested = round(max(current_fee_tvl * 0.6, 0.001), 4)  # reduce by 40%, floor at 0.001
        direction = "lowering" if suggested < current_fee_tvl else "raising"
        analysis["recommendations"].append({
            "parameter": "minFeeActiveTvlRatio",
            "current": current_fee_tvl,
            "suggested": suggested,
            "reason": f"Safety block rejecting {rejection_counts['safety_block']} candidates — consider {direction} threshold from {current_fee_tvl} to {suggested}"
        })
    
    if analysis["deploy_rate"] < 0.2 and len(cycles) > 3:
        analysis["recommendations"].append({
            "parameter": "general",
            "reason": f"Deploy rate {analysis['deploy_rate']:.0%} — consider relaxing screening thresholds"
        })
    
    return analysis

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Meridian Screening Tracker")
    parser.add_argument("--parse", action="store_true", help="Parse latest log files")
    parser.add_argument("--analyze", action="store_true", help="Analyze collected data")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--hours", type=int, default=24, help="Hours of data to analyze")
    args = parser.parse_args()
    
    tracker = load_tracker()
    
    if args.parse:
        # Parse both PM2 logs and agent logs
        today = datetime.now().strftime("%Y-%m-%d")
        agent_log = LOGS_DIR / f"agent-{today}.log"
        
        all_cycles = []
        for log_path in [PM2_LOG, agent_log]:
            cycles = parse_log_file(log_path)
            if cycles:
                all_cycles.extend(cycles)
        
        if all_cycles:
            # Deduplicate by timestamp
            existing_timestamps = {c["timestamp"] for c in tracker["cycles"]}
            new_cycles = [c for c in all_cycles if c["timestamp"] not in existing_timestamps]
            tracker["cycles"].extend(new_cycles)
            
            # Extract candidates
            for cycle in new_cycles:
                tracker["candidates"].extend(cycle.get("candidates", []))
            
            save_tracker(tracker)
            print(f"Parsed {len(new_cycles)} new cycles (total: {len(tracker['cycles'])})")
        else:
            print("No new cycles found")
    
    if args.analyze:
        analysis = analyze_data(tracker)
        with open(ANALYSIS_FILE, "w") as f:
            json.dump(analysis, f, indent=2)
        print(json.dumps(analysis, indent=2))
    
    if args.report:
        analysis = analyze_data(tracker)

        print("\n" + "="*50)
        print("📊 MERIDIAN SCREENING REPORT")
        print("="*50)
        if analysis.get("insufficient_data"):
            print("⚠️  Insufficient data — no screening cycles tracked yet.")
            print("Run --parse first to collect data from logs.")
            print("="*50)
            return
        print(f"Total cycles: {analysis['total_cycles']}")
        print(f"Total candidates: {analysis['total_candidates']}")
        print(f"Deploy rate: {analysis['deploy_rate']:.0%}")
        print(f"Avg bot %: {analysis['avg_bot_pct']}%")
        print(f"Avg fee/TVL rejected: {analysis['avg_fee_tvl_rejected']}%")
        
        if analysis.get("rejection_counts"):
            print("\nRejections by filter:")
            for reason, count in analysis["rejection_counts"].items():
                print(f"  {reason}: {count}")
        
        if analysis.get("recommendations"):
            print("\n💡 Recommendations:")
            for rec in analysis["recommendations"]:
                print(f"  • {rec.get('parameter', 'general')}: {rec.get('reason', '')}")
                if 'suggested' in rec:
                    print(f"    Current: {rec['current']} → Suggested: {rec['suggested']}")
        
        print("="*50)

if __name__ == "__main__":
    main()
