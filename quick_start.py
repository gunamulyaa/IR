#!/usr/bin/env python3
"""
🚀 Quick Start - IR System
==========================

Simple script to run your Information Retrieval system.
No setup required - just run this file!
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the IR system"""
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("🚀 Starting Information Retrieval System...")
    print(f"📁 Project directory: {project_dir}")
    
    # Use the virtual environment Python if it exists
    venv_python = project_dir / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        python_cmd = str(venv_python)
        print(f"✅ Using virtual environment: {python_cmd}")
    else:
        python_cmd = sys.executable
        print(f"⚠️ Using system Python: {python_cmd}")
    
    # Run the Streamlit app
    print("\n📱 Starting web application...")
    print("🌐 App will open at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([
            python_cmd, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ], check=True)
    except subprocess.CalledProcessError:
        print("\n❌ Failed to start app. Make sure Streamlit is installed:")
        print("   pip install streamlit")
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
