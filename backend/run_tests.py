#!/usr/bin/env python3
"""
Test runner script for the math_agent tests.
"""

import subprocess
import sys
import os


def run_tests():
    """Run the tests with coverage."""
    print("🧮 Running Tests")
    print("=" * 50)

    # Change to the backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Run tests with coverage
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests",
        "--cov=app",
        "--cov-report=term-missing",
        "-v",
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
