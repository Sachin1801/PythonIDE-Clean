#!/usr/bin/env python3
"""
Fix EFS directories via the migration API endpoint
"""
import requests
import json
import time
import sys

def check_deployment_status(url):
    """Check if the deployment is ready"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def fix_directories(url):
    """Run the directory fix via API"""
    print(f"Attempting to fix directories via {url}")
    print("-" * 60)
    
    payload = {
        "secret": "PythonIDE2025Migration",
        "action": "fix_directories"
    }
    
    try:
        response = requests.post(
            f"{url}/api/admin/migrate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Directory fix successful!")
                print(f"Output:\n{data.get('output', 'No output available')}")
                return True
            else:
                print(f"❌ Directory fix failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out (this might mean it's still processing)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    urls = [
        "http://pythonide-classroom.tech",
        "http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com"
    ]
    
    print("=" * 60)
    print("EFS DIRECTORY FIX TOOL")
    print("=" * 60)
    print()
    
    # Wait for deployment with status updates
    print("Checking deployment status...")
    max_wait = 720  # 12 minutes
    check_interval = 30  # Check every 30 seconds
    waited = 0
    
    while waited < max_wait:
        for url in urls:
            if check_deployment_status(url):
                print(f"\n✅ Deployment ready at {url}")
                print("\nRunning directory fix...")
                print("=" * 60)
                
                if fix_directories(url):
                    print("\n" + "=" * 60)
                    print("DIRECTORY FIX COMPLETE!")
                    print("=" * 60)
                    print("\nTest with:")
                    print(f"  URL: {url}")
                    print("  Username: admin_editor")
                    print("  Password: XuR0ibQqhw6#")
                    return 0
                else:
                    print("\n⚠️  Directory fix failed. You may need to run it manually.")
                    return 1
        
        # Not ready yet
        remaining = max_wait - waited
        print(f"⏳ Deployment not ready. Waiting... ({remaining} seconds remaining)")
        time.sleep(check_interval)
        waited += check_interval
    
    print("\n❌ Timeout waiting for deployment. Please run this script again later.")
    return 1

if __name__ == "__main__":
    sys.exit(main())