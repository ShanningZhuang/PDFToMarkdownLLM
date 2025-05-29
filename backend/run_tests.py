#!/usr/bin/env python3
"""
Test runner script for PDF to Markdown converter backend
Provides easy access to different testing scenarios
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd: list, description: str):
    """Run a command and handle output."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test runner for PDF to Markdown backend")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage")
    parser.add_argument("--html", action="store_true", help="Generate HTML test report")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--debug", action="store_true", help="Debug mode (show print statements)")
    parser.add_argument("--fast", action="store_true", help="Run only fast tests")
    parser.add_argument("--file", type=str, help="Run specific test file")
    parser.add_argument("--function", type=str, help="Run specific test function")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies first")
    parser.add_argument("--no-capture", "-s", action="store_true", help="Don't capture output (show print statements)")
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Tests directory not found. Make sure you're in the backend directory.")
        sys.exit(1)
    
    success = True
    
    # Install dependencies if requested
    if args.install_deps:
        success &= run_command(
            [sys.executable, "-m", "pip", "install", "-r", "test_requirements.txt"],
            "Installing test dependencies"
        )
        if not success:
            sys.exit(1)
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add specific file if requested
    if args.file:
        if not args.file.startswith("tests/"):
            args.file = f"tests/{args.file}"
        if not args.file.endswith(".py"):
            args.file = f"{args.file}.py"
        cmd.append(args.file)
    
    # Add specific function if requested
    if args.function:
        if args.file:
            cmd[-1] = f"{cmd[-1]}::{args.function}"
        else:
            cmd.append(f"-k {args.function}")
    
    # Add options
    if args.verbose:
        cmd.append("-v")
    
    if args.debug or args.no_capture:
        cmd.append("-s")  # Don't capture output
    
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing"])
        if args.html:
            cmd.append("--cov-report=html")
    
    if args.html and not args.coverage:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    # Add default options for better output
    if not args.debug and not args.no_capture:
        cmd.extend(["--tb=short"])
    else:
        cmd.extend(["--tb=long"])  # More detailed tracebacks in debug mode
    
    cmd.append("--durations=10")
    
    # Run the tests
    description = "Running pytest"
    if args.file:
        description += f" for {args.file}"
    if args.function:
        description += f"::{args.function}"
    if args.coverage:
        description += " with coverage"
    if args.parallel:
        description += " in parallel"
    if args.debug:
        description += " in debug mode"
    
    success &= run_command(cmd, description)
    
    # Show results
    if success:
        print("\n🎉 All tests completed successfully!")
        if args.coverage and args.html:
            print("📊 Coverage report generated: htmlcov/index.html")
        if args.html and not args.coverage:
            print("📋 Test report generated: test_report.html")
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main() 