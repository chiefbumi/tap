#!/usr/bin/env python3
"""
Installation script for Smart Shower OS
Sets up the system with all dependencies and configuration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True


def install_system_dependencies():
    """Install system dependencies"""
    print("\n📦 Installing system dependencies...")
    
    # Update package list
    if not run_command("sudo apt update", "Updating package list"):
        return False
    
    # Install system packages
    packages = [
        "python3-pip",
        "python3-venv",
        "ffmpeg",
        "mpv",
        "bluetooth",
        "bluez",
        "pulseaudio",
        "pulseaudio-module-bluetooth",
        "git",
        "curl",
        "wget"
    ]
    
    for package in packages:
        if not run_command(f"sudo apt install -y {package}", f"Installing {package}"):
            return False
    
    return True


def create_virtual_environment():
    """Create Python virtual environment"""
    print("\n🔧 Setting up Python virtual environment...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    if not run_command("python3 -m venv venv", "Creating virtual environment"):
        return False
    
    return True


def install_python_dependencies():
    """Install Python dependencies"""
    print("\n🐍 Installing Python dependencies...")
    
    # Activate virtual environment and install requirements
    if not run_command("source venv/bin/activate && pip install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command("source venv/bin/activate && pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "logs",
        "config",
        "music",
        "web/static",
        "web/templates",
        "data"
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True


def setup_configuration():
    """Set up configuration files"""
    print("\n⚙️ Setting up configuration...")
    
    # Create default configuration files
    config_dir = Path("config")
    
    # Create settings.yaml if it doesn't exist
    settings_file = config_dir / "settings.yaml"
    if not settings_file.exists():
        print("📝 Creating default settings.yaml...")
        # The ConfigManager will create this automatically
    
    # Create credentials.yaml if it doesn't exist
    credentials_file = config_dir / "credentials.yaml"
    if not credentials_file.exists():
        print("📝 Creating default credentials.yaml...")
        # The ConfigManager will create this automatically
    
    return True


def setup_bluetooth():
    """Set up Bluetooth configuration"""
    print("\n🔵 Setting up Bluetooth...")
    
    # Enable Bluetooth service
    if not run_command("sudo systemctl enable bluetooth", "Enabling Bluetooth service"):
        return False
    
    if not run_command("sudo systemctl start bluetooth", "Starting Bluetooth service"):
        return False
    
    return True


def setup_audio():
    """Set up audio configuration"""
    print("\n🔊 Setting up audio...")
    
    # Configure PulseAudio for Bluetooth
    pulse_config = """
load-module module-bluetooth-discover
load-module module-bluetooth-policy
"""
    
    pulse_config_path = Path.home() / ".config/pulse/default.pa"
    pulse_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(pulse_config_path, "w") as f:
        f.write(pulse_config)
    
    print("✅ Audio configuration created")
    return True


def create_service_file():
    """Create systemd service file"""
    print("\n🔧 Creating systemd service...")
    
    service_content = """[Unit]
Description=Smart Shower OS
After=network.target bluetooth.service

[Service]
Type=simple
User=pi
WorkingDirectory={working_dir}
Environment=PATH={working_dir}/venv/bin
ExecStart={working_dir}/venv/bin/python {working_dir}/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
""".format(working_dir=os.getcwd())
    
    service_file = Path("/etc/systemd/system/smart-shower.service")
    
    try:
        with open(service_file, "w") as f:
            f.write(service_content)
        print("✅ Systemd service file created")
        return True
    except PermissionError:
        print("⚠️ Could not create systemd service file (requires sudo)")
        return False


def setup_permissions():
    """Set up file permissions"""
    print("\n🔐 Setting up permissions...")
    
    # Make main.py executable
    main_py = Path("main.py")
    if main_py.exists():
        main_py.chmod(0o755)
        print("✅ Made main.py executable")
    
    # Set log directory permissions
    logs_dir = Path("logs")
    if logs_dir.exists():
        logs_dir.chmod(0o755)
        print("✅ Set logs directory permissions")
    
    return True


def run_tests():
    """Run basic tests"""
    print("\n🧪 Running tests...")
    
    # Test Python imports
    test_script = """
import sys
sys.path.append('.')

try:
    from utils.config_manager import ConfigManager
    from core.water_control import WaterController
    from core.audio_manager import AudioManager
    from core.safety_monitor import SafetyMonitor
    print("✅ All core modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""
    
    if not run_command(f"source venv/bin/activate && python -c \"{test_script}\"", "Testing imports"):
        return False
    
    return True


def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Configure your API credentials in config/credentials.yaml")
    print("2. Edit settings in config/settings.yaml if needed")
    print("3. Test the system: python main.py")
    print("4. Access the web interface: http://localhost:8082")
    print("5. Use the mobile interface: http://localhost:8082/mobile")
    print("\n🔧 Optional setup:")
    print("- Enable systemd service: sudo systemctl enable smart-shower")
    print("- Start systemd service: sudo systemctl start smart-shower")
    print("- View logs: sudo journalctl -u smart-shower -f")


def main():
    """Main installation function"""
    print("🚿 Smart Shower OS - Installation Script")
    print("=" * 50)
    
    # Check if running as root
    if os.geteuid() == 0:
        print("⚠️ Warning: Running as root. Consider running as a regular user.")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install system dependencies
    if not install_system_dependencies():
        print("❌ Failed to install system dependencies")
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        print("❌ Failed to create virtual environment")
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("❌ Failed to create directories")
        sys.exit(1)
    
    # Setup configuration
    if not setup_configuration():
        print("❌ Failed to setup configuration")
        sys.exit(1)
    
    # Setup Bluetooth
    if not setup_bluetooth():
        print("❌ Failed to setup Bluetooth")
        sys.exit(1)
    
    # Setup audio
    if not setup_audio():
        print("❌ Failed to setup audio")
        sys.exit(1)
    
    # Create service file
    create_service_file()  # Optional, don't fail if this doesn't work
    
    # Setup permissions
    if not setup_permissions():
        print("❌ Failed to setup permissions")
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        print("❌ Tests failed")
        sys.exit(1)
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main() 