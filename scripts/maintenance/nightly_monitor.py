#!/usr/bin/env python3
"""
Nightly Hyperopt Monitor and Reporter
=====================================

Monitors nightly hyperparameter optimization results and generates reports.
Can be run manually or scheduled to check results and send notifications.

Features:
- Check for new optimization results
- Compare with previous best parameters
- Generate summary reports
- Send Telegram notifications (if configured)
- Validate data freshness
- Check system resources

Usage:
    python scripts/nightly_monitor.py --check-results
    python scripts/nightly_monitor.py --send-report --telegram
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)


class NightlyMonitor:
    """Monitor and report on nightly hyperparameter optimization results."""

    def __init__(self):
        self.base_dir = Path("user_data")
        self.nightly_dir = self.base_dir / "nightly_hyperopt"
        self.results_dir = self.nightly_dir

        # Ensure directories exist
        self.nightly_dir.mkdir(parents=True, exist_ok=True)

        # Telegram configuration (optional)
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def check_new_results(self, hours_threshold: int = 24) -> tuple[bool, list[Path]]:
        """
        Check for new optimization results in the last N hours.

        Args:
            hours_threshold: Hours to consider as "new"

        Returns:
            Tuple of (has_new_results, list_of_result_files)
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_threshold)
        new_results = []

        # Check for result files
        result_patterns = [
            "full_results_nightly.json",
            "best_params_nightly.json",
            "optimization_report.md",
            "intermediate_results_*.json",
        ]

        for pattern in result_patterns:
            for result_file in self.results_dir.glob(pattern):
                if result_file.is_file():
                    mtime = datetime.fromtimestamp(result_file.stat().st_mtime)
                    if mtime > cutoff_time:
                        new_results.append(result_file)

        # Remove duplicates by stem
        unique_results = []
        seen_stems = set()
        for result in new_results:
            stem = result.stem
            if stem not in seen_stems:
                seen_stems.add(stem)
                unique_results.append(result)

        has_new = len(unique_results) > 0
        return has_new, unique_results

    def load_latest_results(self) -> dict[str, Any] | None:
        """Load the latest optimization results."""
        result_files = list(self.results_dir.glob("full_results_nightly.json"))
        if not result_files:
            logger.warning("No full_results_nightly.json found")
            return None

        # Get the most recent file
        latest_file = max(result_files, key=lambda f: f.stat().st_mtime)

        try:
            with open(latest_file) as f:
                results = json.load(f)

            # Add file metadata
            results["_metadata"] = {
                "file_path": str(latest_file),
                "modified_time": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
                "file_size_kb": latest_file.stat().st_size / 1024,
            }

            return results
        except Exception as e:
            logger.error(f"Error loading results from {latest_file}: {e}")
            return None

    def compare_with_previous(self, current_results: dict[str, Any]) -> dict[str, Any]:
        """
        Compare current results with previous best (3-year model).

        Args:
            current_results: Current optimization results

        Returns:
            Dictionary with comparison metrics
        """
        comparison = {
            "current_sharpe": current_results.get("best_value", 0),
            "previous_sharpe": None,
            "improvement_pct": None,
            "parameter_changes": {},
            "has_improvement": False,
        }

        # Load previous 3-year results
        previous_params_path = self.base_dir / "model_best_params_3y.json"
        previous_results_path = self.base_dir / "hyperopt_results_3y.json"

        previous_params = None
        previous_sharpe = None

        # Load previous parameters
        if previous_params_path.exists():
            try:
                with open(previous_params_path) as f:
                    previous_params = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load previous parameters: {e}")

        # Load previous Sharpe ratio
        if previous_results_path.exists():
            try:
                with open(previous_results_path) as f:
                    prev_results = json.load(f)
                    previous_sharpe = prev_results.get("best_value")
            except Exception as e:
                logger.warning(f"Could not load previous results: {e}")

        comparison["previous_sharpe"] = previous_sharpe

        # Calculate improvement
        if previous_sharpe is not None and comparison["current_sharpe"] is not None:
            if abs(previous_sharpe) > 0.0001:  # Avoid division by zero
                improvement_pct = (
                    (comparison["current_sharpe"] - previous_sharpe) / abs(previous_sharpe) * 100
                )
                comparison["improvement_pct"] = improvement_pct
                comparison["has_improvement"] = improvement_pct > 5.0  # 5% threshold

        # Compare parameters
        if previous_params and "best_params" in current_results:
            current_params = current_results["best_params"]

            for param in set(list(current_params.keys()) + list(previous_params.keys())):
                curr_val = current_params.get(param)
                prev_val = previous_params.get(param)

                if curr_val is not None and prev_val is not None:
                    if isinstance(curr_val, (int, float)) and isinstance(prev_val, (int, float)):
                        if abs(prev_val) > 0.0001:
                            change_pct = (curr_val - prev_val) / abs(prev_val) * 100
                            comparison["parameter_changes"][param] = {
                                "current": curr_val,
                                "previous": prev_val,
                                "change_pct": change_pct,
                                "significant": abs(change_pct) > 10.0,  # 10% change threshold
                            }
                    else:
                        comparison["parameter_changes"][param] = {
                            "current": curr_val,
                            "previous": prev_val,
                            "change_pct": None,
                            "significant": str(curr_val) != str(prev_val),
                        }

        return comparison

    def generate_summary(self, results: dict[str, Any], comparison: dict[str, Any]) -> str:
        """
        Generate human-readable summary of results.

        Args:
            results: Optimization results
            comparison: Comparison with previous

        Returns:
            Summary string
        """
        summary_lines = []

        # Basic info
        summary_lines.append("📊 NIGHTLY HYPEROPT RESULTS")
        summary_lines.append("=" * 40)

        if "_metadata" in results:
            file_time = results["_metadata"]["modified_time"]
            summary_lines.append(f"📅 Date: {file_time}")

        summary_lines.append(f"🎯 Best Sharpe Ratio: {results.get('best_value', 0):.4f}")
        summary_lines.append(f"🔬 Total Trials: {results.get('total_trials', 0)}")

        # Resource usage
        if "resource_stats" in results:
            stats = results["resource_stats"]
            summary_lines.append(f"⏱️  Duration: {stats.get('elapsed_hours', 0):.2f}h")
            summary_lines.append(f"💾 Memory: {stats.get('memory_used_gb', 0):.1f}GB")
            summary_lines.append(f"💿 Disk Free: {stats.get('disk_free_gb', 0):.1f}GB")

        # Comparison
        summary_lines.append("\n📈 COMPARISON WITH PREVIOUS BEST")
        summary_lines.append("-" * 40)

        if comparison["previous_sharpe"] is not None:
            prev_sharpe = comparison["previous_sharpe"]
            curr_sharpe = comparison["current_sharpe"]
            improvement = comparison["improvement_pct"]

            summary_lines.append(f"Previous Sharpe: {prev_sharpe:.4f}")
            summary_lines.append(f"Current Sharpe:  {curr_sharpe:.4f}")

            if improvement is not None:
                arrow = "📈" if improvement > 0 else "📉"
                summary_lines.append(f"{arrow} Improvement: {improvement:+.1f}%")

                if comparison["has_improvement"]:
                    summary_lines.append("✅ SIGNIFICANT IMPROVEMENT DETECTED!")
                    summary_lines.append("   Consider updating model parameters.")
                else:
                    summary_lines.append("⚠️  Improvement below 5% threshold")
                    summary_lines.append("   Keep current parameters.")
        else:
            summary_lines.append("No previous results found for comparison.")

        # Significant parameter changes
        significant_changes = {
            k: v for k, v in comparison["parameter_changes"].items() if v.get("significant", False)
        }

        if significant_changes:
            summary_lines.append("\n🔧 SIGNIFICANT PARAMETER CHANGES")
            summary_lines.append("-" * 40)

            for param, change in significant_changes.items():
                curr = change["current"]
                prev = change["previous"]
                pct = change.get("change_pct")

                if pct is not None:
                    summary_lines.append(f"{param}: {prev:.4f} → {curr:.4f} ({pct:+.1f}%)")
                else:
                    summary_lines.append(f"{param}: {prev} → {curr}")

        # Recommendations
        summary_lines.append("\n💡 RECOMMENDATIONS")
        summary_lines.append("-" * 40)

        if comparison["has_improvement"]:
            summary_lines.append("1. ✅ Update model with new parameters")
            summary_lines.append("2. 📊 Run backtest with new parameters")
            summary_lines.append("3. 🚀 Consider deploying to paper trading")
        else:
            summary_lines.append("1. ⚠️  Keep current parameters")
            summary_lines.append("2. 🔄 Continue monitoring")
            summary_lines.append("3. 📅 Schedule next optimization in 3 days")

        summary_lines.append("\n📁 Results location: user_data/nightly_hyperopt/")

        return "\n".join(summary_lines)

    def send_telegram_notification(self, message: str):
        """Send notification via Telegram (if configured)."""
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning(
                "Telegram credentials not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables."
            )
            return False

        try:
            import requests

            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {"chat_id": self.telegram_chat_id, "text": message, "parse_mode": "Markdown"}

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info("Telegram notification sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False

    def check_data_freshness(self, max_age_hours: int = 24) -> tuple[bool, str]:
        """
        Check if data is fresh enough for next optimization.

        Args:
            max_age_hours: Maximum age of data in hours

        Returns:
            Tuple of (is_fresh, message)
        """
        try:
            # Check for data files
            data_dir = self.base_dir / "data" / "binance"
            if not data_dir.exists():
                return False, f"Data directory not found: {data_dir}"

            # Find most recent data file
            data_files = list(data_dir.glob("*.feather"))
            if not data_files:
                return False, "No data files found"

            latest_file = max(data_files, key=lambda f: f.stat().st_mtime)
            file_age_hours = (time.time() - latest_file.stat().st_mtime) / 3600

            if file_age_hours > max_age_hours:
                return False, f"Data is {file_age_hours:.1f} hours old (max: {max_age_hours}h)"

            return True, f"Data is fresh ({file_age_hours:.1f} hours old)"

        except Exception as e:
            return False, f"Error checking data freshness: {e}"

    def check_system_resources(self) -> dict[str, Any]:
        """Check system resources for next optimization."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(".")

            return {
                "timestamp": datetime.now().isoformat(),
                "memory_used_gb": memory.used / (1024**3),
                "memory_percent": memory.percent,
                "disk_free_gb": disk.free / (1024**3),
                "disk_percent": disk.percent,
                "cpu_percent": psutil.cpu_percent(interval=1),
                "has_enough_resources": memory.percent < 90 and disk.percent < 90,
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {"error": str(e), "has_enough_resources": False}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor and report on nightly hyperparameter optimization"
    )

    parser.add_argument(
        "--check-results", action="store_true", help="Check for new optimization results"
    )
    parser.add_argument("--send-report", action="store_true", help="Generate and send report")
    parser.add_argument(
        "--telegram", action="store_true", help="Send report via Telegram (requires credentials)"
    )
    parser.add_argument("--check-data", action="store_true", help="Check data freshness")
    parser.add_argument("--check-resources", action="store_true", help="Check system resources")
    parser.add_argument(
        "--hours-threshold",
        type=int,
        default=24,
        help='Hours threshold for "new" results (default: 24)',
    )
    parser.add_argument("--output-file", type=str, help="Save report to file")

    args = parser.parse_args()

    # If no specific action specified, do all checks
    if not any([args.check_results, args.send_report, args.check_data, args.check_resources]):
        args.check_results = True
        args.send_report = True
        args.check_data = True

    monitor = NightlyMonitor()

    print("\n" + "=" * 60)
    print("🌙 NIGHTLY HYPEROPT MONITOR")
    print("=" * 60)

    results_summary = {}

    # Check for new results
    if args.check_results:
        print("\n🔍 Checking for new results...")
        has_new, new_files = monitor.check_new_results(hours_threshold=args.hours_threshold)

        if has_new:
            print(f"✅ Found {len(new_files)} new result(s):")
            for f in new_files:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                print(f"   • {f.name} ({mtime.strftime('%Y-%m-%d %H:%M')})")

            # Load latest results
            results = monitor.load_latest_results()
            if results:
                comparison = monitor.compare_with_previous(results)
                summary = monitor.generate_summary(results, comparison)

                results_summary = {
                    "has_new": True,
                    "results": results,
                    "comparison": comparison,
                    "summary": summary,
                }

                print("\n📊 Latest Results Summary:")
                print("-" * 40)
                print(summary)

                # Save to file if requested
                if args.output_file:
                    output_path = Path(args.output_file)
                    with open(output_path, "w") as f:
                        json.dump(
                            {
                                "results": results,
                                "comparison": comparison,
                                "summary": summary,
                                "timestamp": datetime.now().isoformat(),
                            },
                            f,
                            indent=2,
                        )
                    print(f"\n💾 Saved full report to: {output_path}")
            else:
                print("⚠️  Could not load results")
                results_summary["has_new"] = False
        else:
            print(f"⏳ No new results found in the last {args.hours_threshold} hours")
            results_summary["has_new"] = False

    # Send report
    if args.send_report and results_summary.get("has_new"):
        print("\n📨 Sending report...")

        if args.telegram:
            if results_summary.get("summary"):
                success = monitor.send_telegram_notification(results_summary["summary"])
                if success:
                    print("✅ Telegram notification sent")
                else:
                    print("⚠️  Failed to send Telegram notification")
            else:
                print("⚠️  No summary to send")
        else:
            print("ℹ️  Telegram not requested (use --telegram to send)")

    # Check data freshness
    if args.check_data:
        print("\n📊 Checking data freshness...")
        is_fresh, message = monitor.check_data_freshness()
        if is_fresh:
            print(f"✅ {message}")
        else:
            print(f"⚠️  {message}")
            print("   Consider running: python scripts/download_data.py")

    # Check system resources
    if args.check_resources:
        print("\n💻 Checking system resources...")
        resources = monitor.check_system_resources()

        if "error" in resources:
            print(f"⚠️  Error: {resources['error']}")
        else:
            print(
                f"💾 Memory: {resources['memory_used_gb']:.1f}GB ({resources['memory_percent']:.1f}%)"
            )
            print(
                f"💿 Disk: {resources['disk_free_gb']:.1f}GB free ({resources['disk_percent']:.1f}% used)"
            )
            print(f"⚡ CPU: {resources['cpu_percent']:.1f}%")

            if resources["has_enough_resources"]:
                print("✅ System has enough resources for next optimization")
            else:
                print("⚠️  System resources may be insufficient for optimization")
                print("   Consider freeing up memory or disk space")

    print("\n" + "=" * 60)
    print("✅ MONITORING COMPLETE")
    print("=" * 60)

    # Return exit code based on findings
    if results_summary.get("has_new") and results_summary.get("comparison", {}).get(
        "has_improvement"
    ):
        return 0  # Success with improvement
    elif results_summary.get("has_new"):
        return 1  # Success but no significant improvement
    else:
        return 2  # No new results


if __name__ == "__main__":
    import time

    sys.exit(main())
