#!/usr/bin/env python3
"""
ZeroLag Installation Script

This script automates the installation of ZeroLag and its dependencies
across different operating systems and Python versions.
"""

import sys
import os
import subprocess
import platform
import shutil
from pathlib import Path


class ZeroLagInstaller:
    """ZeroLag installation manager."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.install_dir = Path.cwd()
        self.venv_dir = self.install_dir / "venv"
        self.requirements_file = self.install_dir / "requirements.txt"
        
    def check_requirements(self):
        """Check system requirements."""
        print("Checking system requirements...")
        
        # Check Python version
        if self.python_version < (3, 8):
            print(f"❌ Python 3.8+ required, found {self.python_version.major}.{self.python_version.minor}")
            return False
        else:
            print(f"✅ Python {self.python_version.major}.{self.python_version.minor} detected")
        
        # Check operating system
        supported_systems = ['windows', 'linux', 'darwin']
        if self.system not in supported_systems:
            print(f"❌ Unsupported operating system: {self.system}")
            return False
        else:
            print(f"✅ Operating system: {self.system}")
        
        # Check available space
        free_space = shutil.disk_usage(self.install_dir).free
        required_space = 100 * 1024 * 1024  # 100MB
        if free_space < required_space:
            print(f"❌ Insufficient disk space: {free_space // (1024*1024)}MB available, {required_space // (1024*1024)}MB required")
            return False
        else:
            print(f"✅ Sufficient disk space: {free_space // (1024*1024)}MB available")
        
        return True
    
    def create_virtual_environment(self):
        """Create virtual environment."""
        print("Creating virtual environment...")
        
        if self.venv_dir.exists():
            print("Virtual environment already exists, skipping...")
            return True
        
        try:
            subprocess.run([
                sys.executable, "-m", "venv", str(self.venv_dir)
            ], check=True)
            print("✅ Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    def get_pip_command(self):
        """Get pip command for virtual environment."""
        if self.system == "windows":
            return str(self.venv_dir / "Scripts" / "pip.exe")
        else:
            return str(self.venv_dir / "bin" / "pip")
    
    def get_python_command(self):
        """Get Python command for virtual environment."""
        if self.system == "windows":
            return str(self.venv_dir / "Scripts" / "python.exe")
        else:
            return str(self.venv_dir / "bin" / "python")
    
    def install_dependencies(self):
        """Install Python dependencies."""
        print("Installing dependencies...")
        
        pip_cmd = self.get_pip_command()
        
        # Upgrade pip first
        try:
            subprocess.run([
                pip_cmd, "install", "--upgrade", "pip"
            ], check=True)
            print("✅ pip upgraded")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to upgrade pip: {e}")
        
        # Install requirements
        if self.requirements_file.exists():
            try:
                subprocess.run([
                    pip_cmd, "install", "-r", str(self.requirements_file)
                ], check=True)
                print("✅ Dependencies installed from requirements.txt")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install requirements: {e}")
                return False
        else:
            # Install core dependencies manually
            core_deps = [
                "PyQt5>=5.15.0",
                "pynput>=1.7.6",
                "psutil>=5.8.0"
            ]
            
            # Add system-specific dependencies
            if self.system == "windows":
                core_deps.append("pywin32>=227")
            elif self.system == "darwin":
                core_deps.append("pyobjc>=8.0")
            
            try:
                for dep in core_deps:
                    subprocess.run([
                        pip_cmd, "install", dep
                    ], check=True)
                print("✅ Core dependencies installed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install core dependencies: {e}")
                return False
        
        return True
    
    def create_launcher_scripts(self):
        """Create launcher scripts for different platforms."""
        print("Creating launcher scripts...")
        
        python_cmd = self.get_python_command()
        
        if self.system == "windows":
            # Create batch file
            batch_content = f"""@echo off
cd /d "{self.install_dir}"
"{python_cmd}" run_gui.py
pause
"""
            batch_file = self.install_dir / "run_zerolag.bat"
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            print("✅ Windows launcher created: run_zerolag.bat")
            
            # Create PowerShell script
            ps_content = f"""# ZeroLag Launcher
Set-Location "{self.install_dir}"
& "{python_cmd}" run_gui.py
"""
            ps_file = self.install_dir / "run_zerolag.ps1"
            with open(ps_file, 'w') as f:
                f.write(ps_content)
            print("✅ PowerShell launcher created: run_zerolag.ps1")
            
        else:
            # Create shell script
            shell_content = f"""#!/bin/bash
cd "{self.install_dir}"
"{python_cmd}" run_gui.py
"""
            shell_file = self.install_dir / "run_zerolag.sh"
            with open(shell_file, 'w') as f:
                f.write(shell_content)
            
            # Make executable
            os.chmod(shell_file, 0o755)
            print("✅ Unix launcher created: run_zerolag.sh")
    
    def create_desktop_shortcut(self):
        """Create desktop shortcut (Windows only)."""
        if self.system != "windows":
            return
        
        print("Creating desktop shortcut...")
        
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "ZeroLag.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = str(self.install_dir / "run_zerolag.bat")
            shortcut.WorkingDirectory = str(self.install_dir)
            shortcut.IconLocation = str(self.install_dir / "assets" / "icon.ico")
            shortcut.save()
            
            print("✅ Desktop shortcut created")
        except ImportError:
            print("⚠️  Desktop shortcut creation skipped (winshell not available)")
        except Exception as e:
            print(f"⚠️  Failed to create desktop shortcut: {e}")
    
    def setup_configuration(self):
        """Setup initial configuration."""
        print("Setting up configuration...")
        
        # Create config directory
        config_dir = self.install_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Create profiles directory
        profiles_dir = self.install_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)
        
        # Create logs directory
        logs_dir = self.install_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Create default configuration
        default_config = {
            "version": "1.0.0",
            "settings": {
                "smoothing": {
                    "enabled": True,
                    "factor": 0.5
                },
                "anti_ghosting": {
                    "enabled": True
                },
                "nkro": {
                    "enabled": True
                },
                "dpi": {
                    "enabled": True,
                    "target_dpi": 800
                }
            }
        }
        
        import json
        config_file = config_dir / "default.json"
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print("✅ Configuration files created")
    
    def run_tests(self):
        """Run basic tests to verify installation."""
        print("Running installation tests...")
        
        python_cmd = self.get_python_command()
        
        try:
            # Test import
            subprocess.run([
                python_cmd, "-c", "import PyQt5; import pynput; import psutil; print('✅ All imports successful')"
            ], check=True)
            
            # Test GUI creation
            test_script = """
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

app = QApplication(sys.argv)
print('✅ GUI framework working')
app.quit()
"""
            subprocess.run([
                python_cmd, "-c", test_script
            ], check=True)
            
            print("✅ Installation tests passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation tests failed: {e}")
            return False
    
    def install(self):
        """Run complete installation process."""
        print("=" * 60)
        print("ZeroLag Installation Script")
        print("=" * 60)
        
        # Check requirements
        if not self.check_requirements():
            print("❌ Installation failed: Requirements not met")
            return False
        
        # Create virtual environment
        if not self.create_virtual_environment():
            print("❌ Installation failed: Could not create virtual environment")
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            print("❌ Installation failed: Could not install dependencies")
            return False
        
        # Create launcher scripts
        self.create_launcher_scripts()
        
        # Create desktop shortcut (Windows)
        self.create_desktop_shortcut()
        
        # Setup configuration
        self.setup_configuration()
        
        # Run tests
        if not self.run_tests():
            print("⚠️  Installation completed with warnings")
        else:
            print("✅ Installation completed successfully")
        
        print("\n" + "=" * 60)
        print("Installation Complete!")
        print("=" * 60)
        print(f"Installation directory: {self.install_dir}")
        print(f"Virtual environment: {self.venv_dir}")
        
        if self.system == "windows":
            print("\nTo run ZeroLag:")
            print("1. Double-click 'run_zerolag.bat'")
            print("2. Or run 'run_zerolag.ps1' in PowerShell")
            print("3. Or run 'python run_gui.py' in command prompt")
        else:
            print("\nTo run ZeroLag:")
            print("1. Run './run_zerolag.sh'")
            print("2. Or run 'python run_gui.py'")
        
        print("\nFor more information, see README.md")
        
        return True


def main():
    """Main installation function."""
    installer = ZeroLagInstaller()
    
    try:
        success = installer.install()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
