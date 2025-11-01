#!/usr/bin/env python3
"""
Setup script for Smart Traffic Management System
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_requirements():
    """Install required packages"""
    try:
        print("📦 Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        sys.exit(1)

def setup_environment():
    """Setup environment file if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            print("📝 Creating .env file from template...")
            with open('.env.example', 'r') as src, open('.env', 'w') as dst:
                dst.write(src.read())
            print("✅ .env file created. Please edit it with your credentials.")
        else:
            print("⚠️  .env.example not found. Please create .env manually.")
    else:
        print("✅ .env file already exists")

def check_directories():
    """Check if required directories exist"""
    required_dirs = ['Masks', 'video', 'output']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"📁 Created directory: {dir_name}")
        else:
            print(f"✅ Directory exists: {dir_name}")

def main():
    """Main setup function"""
    print("🚦 Smart Traffic Management System Setup")
    print("=" * 50)
    
    check_python_version()
    install_requirements()
    setup_environment()
    check_directories()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your Twilio credentials")
    print("2. Place YOLO model weights in ../Yolo-Weights/")
    print("3. Run: streamlit run main.py")

if __name__ == "__main__":
    main()