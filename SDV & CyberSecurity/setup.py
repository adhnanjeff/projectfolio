#!/usr/bin/env python3
"""
Setup script for CAN Bus IDS System
Automates the initial setup process
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command with error handling"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def setup_vcan():
    """Setup virtual CAN interface"""
    print("\n🚗 Setting up virtual CAN interface...")
    
    # Check if running on Linux/macOS
    if sys.platform not in ['linux', 'darwin']:
        print("⚠️ Virtual CAN setup is only supported on Linux/macOS")
        print("Please manually configure CAN interface for your system")
        return True
    
    commands = [
        ("sudo modprobe vcan", "Loading vcan kernel module"),
        ("sudo ip link add dev vcan0 type vcan", "Creating vcan0 interface"),
        ("sudo ip link set up vcan0", "Bringing up vcan0 interface")
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            print("⚠️ CAN interface setup failed. You may need to set it up manually.")
            return False
    
    # Verify interface
    if run_command("ip link show vcan0", "Verifying vcan0 interface"):
        print("✅ Virtual CAN interface setup completed")
        return True
    
    return False

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False
    
    return run_command(f"{sys.executable} -m pip install -r requirements.txt", 
                      "Installing dependencies")

def train_model():
    """Train the IDS model"""
    print("\n🧠 Training IDS model...")
    return run_command(f"{sys.executable} train_ids.py", "Training IDS model")

def create_startup_scripts():
    """Create convenient startup scripts"""
    print("\n📝 Creating startup scripts...")
    
    # Start IDS script
    ids_script = """#!/bin/bash
echo "🔍 Starting CAN Bus IDS..."
python ids.py
"""
    
    # Start dashboard script
    dashboard_script = """#!/bin/bash
echo "📊 Starting IDS Dashboard..."
streamlit run dashboard.py
"""
    
    # Start attack engine script
    attack_script = """#!/bin/bash
echo "🎯 Starting Attack Engine..."
python attack_engine.py
"""
    
    # Start normal traffic script
    traffic_script = """#!/bin/bash
echo "🚗 Starting Normal Traffic Generator..."
python sender.py
"""
    
    scripts = [
        ("start_ids.sh", ids_script),
        ("start_dashboard.sh", dashboard_script),
        ("start_attacks.sh", attack_script),
        ("start_traffic.sh", traffic_script)
    ]
    
    try:
        for filename, content in scripts:
            with open(filename, 'w') as f:
                f.write(content)
            os.chmod(filename, 0o755)  # Make executable
        
        print("✅ Startup scripts created")
        return True
    except Exception as e:
        print(f"❌ Failed to create startup scripts: {e}")
        return False

def print_usage_instructions():
    """Print usage instructions"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\n🚀 Quick Start Guide:")
    print("\n1. Start IDS Monitoring:")
    print("   ./start_ids.sh  (or: python ids.py)")
    
    print("\n2. Launch Dashboard (new terminal):")
    print("   ./start_dashboard.sh  (or: streamlit run dashboard.py)")
    
    print("\n3. Generate Normal Traffic (optional, new terminal):")
    print("   ./start_traffic.sh  (or: python sender.py)")
    
    print("\n4. Manual Attack Control (new terminal):")
    print("   ./start_attacks.sh  (or: python attack_engine.py)")
    
    print("\n📊 Dashboard URL: http://localhost:8501")
    print("\n🎯 Attack Types Available:")
    print("   • DoS (Denial of Service)")
    print("   • Fuzzing (Random data injection)")
    print("   • Replay (Message replay attacks)")
    print("   • Spoofing (Fake sensor values)")
    print("   • Flooding (Bus overwhelming)")
    
    print("\n📚 For detailed documentation, see README.md")
    print("="*60)

def main():
    """Main setup function"""
    print("🚗 CAN Bus IDS System Setup")
    print("="*40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Setup virtual CAN (optional, may fail on some systems)
    setup_vcan()
    
    # Train model
    if not train_model():
        print("❌ Setup failed at model training")
        sys.exit(1)
    
    # Create startup scripts
    create_startup_scripts()
    
    # Print usage instructions
    print_usage_instructions()

if __name__ == "__main__":
    main()