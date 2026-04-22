#!/usr/bin/env python3
"""
Google Maps Scraper - Setup Script
Automated setup for installing all dependencies and configuring the environment
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a shell command with error handling"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}: {e.stderr}")
        return False


def install_python_dependencies():
    """Install Python dependencies from requirements.txt"""
    print("🐍 Installing Python dependencies...")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        if not run_command(
            f"{sys.executable} -m pip install -r requirements.txt", 
            "Installing Python dependencies"
        ):
            return False
    else:
        print("❌ requirements.txt not found")
        return False
    
    return True


def install_playwright_browsers():
    """Install Playwright browsers"""
    print("🎭 Installing Playwright browsers...")
    
    if not run_command(f"{sys.executable} -m playwright install chromium", "Installing Chromium browser"):
        return False
    
    if not run_command(f"{sys.executable} -m playwright install-deps chromium", "Installing Chromium dependencies"):
        return False
    
    return True


def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ["output", "logs"]
    
    for directory in directories:
        dir_path = Path(__file__).parent / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📂 Directory already exists: {directory}")
    
    return True


def create_sample_config():
    """Create sample configuration file"""
    print("⚙️  Creating sample configuration...")
    
    config_content = """# Google Maps Scraper Configuration
# You can add your custom settings here

# Default search settings
DEFAULT_MAX_RESULTS=50
DEFAULT_DELAY_MIN=1
DEFAULT_DELAY_MAX=3

# Browser settings
HEADLESS=false
TIMEOUT=30000

# Output settings
OUTPUT_FORMAT=both  # csv, excel, or both
OUTPUT_DIRECTORY=output

# AI Integration
GROQ_API_KEY=your_groq_api_key_here
"""
    
    config_file = Path(__file__).parent / ".env"
    if not config_file.exists():
        with open(config_file, 'w') as f:
            f.write(config_content)
        print("✅ Created sample configuration file: .env")
    else:
        print("📄 Configuration file already exists: .env")
    
    return True


def verify_installation():
    """Verify that all components are properly installed"""
    print("🔍 Verifying installation...")
    
    # Check Python imports
    try:
        import playwright
        import pandas
        import openpyxl
        print("✅ All Python dependencies imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Check Playwright browsers
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
        print("✅ Playwright browsers working correctly")
    except Exception as e:
        print(f"❌ Playwright browser error: {e}")
        return False
    
    return True


def main():
    """Main setup function"""
    print("🚀 Google Maps Scraper Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Run setup steps
    steps = [
        ("Creating directories", create_directories),
        ("Creating sample configuration", create_sample_config),
        ("Installing Python dependencies", install_python_dependencies),
        ("Installing Playwright browsers", install_playwright_browsers),
        ("Verifying installation", verify_installation)
    ]
    
    success = True
    for description, step_func in steps:
        if not step_func():
            print(f"❌ Setup failed at: {description}")
            success = False
            break
        print()
    
    if success:
        print("🎉 Setup completed successfully!")
        print("\n📖 Usage Instructions:")
        print("1. Run the scraper: python main.py 'restaurants in New York'")
        print("2. For headless mode: python main.py 'restaurants in New York' --headless")
        print("3. For more options: python main.py --help")
        print("\n📁 Output files will be saved in the 'output' directory")
    else:
        print("❌ Setup failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
