#!/usr/bin/env python
"""
GreenMind Main Entry Point
Quick start script for launching GreenMind
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check for .env file
    env_file = Path('.env')
    if not env_file.exists():
        print("\n⚠️  .env file not found")
        print("Creating .env from .env.example...")
        
        env_example = Path('.env.example')
        if env_example.exists():
            with open(env_example) as f:
                content = f.read()
            with open('.env', 'w') as f:
                f.write(content)
            print("✓ .env file created")
            print("⚠️  IMPORTANT: Please fill in your API keys in .env file")
        else:
            print("❌ .env.example not found")
            sys.exit(1)
    else:
        print("✓ .env file exists")
    
    # Check for required packages
    print("\n📦 Checking packages...")
    required_packages = [
        'langchain',
        'streamlit',
        'faiss',
        'dotenv',
        'PyPDF2'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    
    return True

def run_tests():
    """Run setup tests"""
    print("\n🧪 Running tests...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'test_setup.py'],
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def setup_project():
    """Run setup script"""
    print("\n⚙️  Setting up project...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'setup.py'],
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error during setup: {e}")
        return False

def launch_app():
    """Launch Streamlit application"""
    print("\n🚀 Launching GreenMind...")
    print("Open your browser at: http://localhost:8501\n")
    
    try:
        subprocess.run(
            [sys.executable, '-m', 'streamlit', 'run', 'src/ui/streamlit_app.py'],
            cwd=Path(__file__).parent
        )
    except KeyboardInterrupt:
        print("\n\nGreenMind shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error launching application: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                     🌍 GreenMind 🌍                       ║
    ║        Intelligent Sustainability Advisor v1.0           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Run checks
    if not check_environment():
        sys.exit(1)
    
    # Optional: Run tests
    print("\n" + "="*60)
    response = input("Run setup tests? (y/n): ").lower().strip()
    if response == 'y':
        if not run_tests():
            print("⚠️  Some tests failed. Continuing anyway...")
    
    # Run setup
    response = input("\nRun project setup? (y/n): ").lower().strip()
    if response == 'y':
        if not setup_project():
            print("❌ Setup failed")
            sys.exit(1)
    
    # Launch
    print("\n" + "="*60)
    print("GreenMind is ready to launch!")
    print("="*60)
    
    launch_app()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGreenMind terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
