#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil

def test_command(command, description):
    print(f"Testing {description}...")
    try:
        result = subprocess.run([command, "version"], capture_output=True, text=True, check=True)
        print(f"✅ {description} is working! Output:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} error: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ {description} not found in PATH")
        return False

def test_script_run():
    print("Testing server.py imports...")
    try:
        # Only import to test dependencies
        import yaml
        from adbdevicemanager import AdbDeviceManager
        print("✅ Required modules can be imported")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    print("Environment test for android-mcp-server")
    print("-" * 50)
    
    # Print current directory
    print(f"Current directory: {os.getcwd()}")
    print("-" * 50)
    
    # Print PATH environment variable
    print(f"PATH environment variable: {os.environ.get('PATH', 'Not set')}")
    print("-" * 50)
    
    # Test ADB
    adb_works = test_command("adb", "ADB")
    print("-" * 50)
    
    # Test UV
    uv_path = shutil.which("uv")
    if uv_path:
        print(f"✅ UV found at: {uv_path}")
    else:
        print("❌ UV not found in PATH")
    print("-" * 50)
    
    # Test Python imports
    imports_work = test_script_run()
    print("-" * 50)
    
    # Check if config.yaml exists
    if os.path.exists("config.yaml"):
        print("✅ config.yaml exists")
        try:
            with open("config.yaml") as f:
                print("config.yaml content:")
                print(f.read())
        except Exception as e:
            print(f"❌ Error reading config.yaml: {e}")
    else:
        print("❌ config.yaml does not exist")
    print("-" * 50)
    
    # Print overall result
    if adb_works and uv_path and imports_work:
        print("🎉 All requirements met! android-mcp-server should work properly.")
    else:
        print("⚠️ Some requirements are missing. Please fix the issues above.")
        
if __name__ == "__main__":
    main() 