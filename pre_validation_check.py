#!/usr/bin/env python3
"""
PRE-VALIDATION HEALTH CHECK
Verify system readiness before running full test suite
"""

import subprocess
import os
import sys
import socket
from pathlib import Path

def check_port_available(port=8000):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def check_python_version():
    """Verify Python 3.8+"""
    version = sys.version_info
    ok = version.major >= 3 and version.minor >= 8
    return ok, f"Python {version.major}.{version.minor}.{version.micro}"

def check_dependencies():
    """Check required Python packages"""
    required = ['requests', 'fastapi', 'pymongo', 'pydantic']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    return len(missing) == 0, missing

def check_backend_file():
    """Check backend startup file exists"""
    path = Path("backend/app_simple.py")
    return path.exists(), str(path)

def check_test_file():
    """Check validation test file"""
    path = Path("complete_business_validation.py")
    return path.exists(), str(path)

def check_mongodb():
    """Check if MongoDB is accessible"""
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=1000)
        client.admin.command('ping')
        client.close()
        return True, "Connected"
    except Exception as e:
        return False, str(e)

def main():
    print("="*70)
    print("PRE-VALIDATION HEALTH CHECK")
    print("="*70)
    print()
    
    checks = {
        "Python Version": check_python_version(),
        "Backend File (app_simple.py)": check_backend_file(),
        "Test File (complete_business_validation.py)": check_test_file(),
        "Dependencies": check_dependencies(),
        "Port 8000 Available": (check_port_available(), "Available" if check_port_available() else "In Use"),
        "MongoDB Connection": check_mongodb(),
    }
    
    passed = 0
    failed = 0
    
    for check_name, result in checks.items():
        if isinstance(result, tuple) and len(result) == 2:
            success, message = result
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} | {check_name}: {message}")
            if success:
                passed += 1
            else:
                failed += 1
        else:
            print(f"⚠️  SKIP | {check_name}: Invalid check")
    
    print()
    print("="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    print()
    
    if failed == 0:
        print("✅ System is ready for validation!")
        print()
        print("Next command:")
        print("  bash run_validation.sh")
        return 0
    elif failed <= 2:
        print("⚠️  Some issues found, but can proceed with caveats:")
        if not check_mongodb()[0]:
            print("  - MongoDB not running: backend may fail")
            print("    Fix: docker run -d -p 27017:27017 mongo:latest")
        if not check_port_available():
            print("  - Port 8000 in use: backend will fail to start")
            print("    Fix: lsof -i :8000 && kill -9 <PID>")
        print()
        print("Continue? (y/n): ", end="")
        if input().lower() != 'y':
            return 1
        return 0
    else:
        print("❌ Critical issues found. Fix before proceeding:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
