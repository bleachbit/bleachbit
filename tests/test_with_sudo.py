#!/usr/bin/env python3
"""
Utility script to discover and run tests marked for sudo execution.
Tests are marked with the @requires_sudo decorator.

Usage:
    make tests-with-sudo
"""

import inspect
import os
import subprocess
import sys
import unittest
from importlib import import_module

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def discover_sudo_tests():
    """Discover all test methods marked with @test_also_with_sudo decorator"""
    sudo_tests = []

    # Import test modules to scan for decorated tests
    test_modules = [
        'tests.TestCLI',
        'tests.TestGeneral',
        'tests.TestUnix',
    ]

    for module_name in test_modules:
        try:
            module = import_module(module_name)

            # Find all test classes in the module
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, unittest.TestCase):
                    # Find all test methods in the class
                    for method_name, method in inspect.getmembers(obj):
                        if (method_name.startswith('test_') and
                                hasattr(method, '_test_also_with_sudo')):
                            test_path = f"{module_name}.{name}.{method_name}"
                            sudo_tests.append(test_path)

        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")

    return sudo_tests


def run_sudo_tests(test_list):
    """Run a list of tests with sudo privileges"""
    if not test_list:
        print("No tests marked with @requires_sudo found")
        return True

    print(f"Found {len(test_list)} tests marked for sudo execution:")
    for test in test_list:
        print(f"  - {test}")

    print(f"\n{'=' * 60}")
    print("Running sudo tests...")
    print('=' * 60)

    base_cmd = [sys.executable, '-m', 'unittest'] + test_list + ['-v']

    if os.name == 'posix' and os.geteuid() == 0:
        sudo_uid = os.getenv('SUDO_UID')
        if sudo_uid and sudo_uid != '0':
            print("\nDetected EUID=0 with SUDO_UID preserved; skipping nested sudo.")
            cmd = base_cmd
        else:
            print("\nERROR: Do not run tests/test_with_sudo.py with sudo or as root.")
            print("Run it unprivileged; it will invoke sudo internally.")
            print("Try: make tests-with-sudo or python3 tests/test_with_sudo.py")
            return False
    else:
        cmd = ['sudo', '-E'] + base_cmd

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running sudo tests: {e}")
        return False


def main():
    """Discover and run all tests marked with @test_also_with_sudo"""
    sudo_tests = discover_sudo_tests()

    if not sudo_tests:
        print("No tests marked with @test_also_with_sudo found")
        sys.exit(0)

    if run_sudo_tests(sudo_tests):
        print("\nAll tests with sudo passed")
        sys.exit(0)
    else:
        print("\nSome tests with sudo failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
