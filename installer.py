#!/usr/bin/env python3
"""
Alex's Personal Hub - Tiny Installer
Downloads and installs the full application.
"""

import os
import sys
import json
import hashlib
import zipfile
import requests
from pathlib import Path
from tqdm import tqdm
import tempfile
import shutil

class AppInstaller:
    def __init__(self):
        # GitHub repository info (change these to your repo)
        self.repo_owner = "yourusername"
        self.repo_name = "alex-personal-hub"
        self.github_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        
        # Local paths
        self.install_dir = Path.home() / "AlexPersonalHub"
        self.temp_dir = Path(tempfile.gettempdir()) / "aph_install"
        
        # File manifest with checksums
        self.manifest = {
            "files": {
                "main_app.py": {"size": 0, "hash": ""},
                "requirements.txt": {"size": 0, "hash": ""},
                "media_config.json": {"size": 0, "hash": ""},
                # Add more files as needed
            },
            "version": "1.0.0",
            "total_size": 0
        }
        
        # Colors for console
        self.COLORS = {
            "HEADER": '\033[95m',
            "BLUE": '\033[94m',
            "CYAN": '\033[96m',
            "GREEN": '\033[92m',
            "YELLOW": '\033[93m',
            "RED": '\033[91m',
            "END": '\033[0m',
            "BOLD": '\033[1m'
        }
    
    def print_banner(self):
        banner = f"""{self.COLORS['CYAN']}
╔══════════════════════════════════════════════════════════════════╗
║{self.COLORS['YELLOW']}          ALEX'S PERSONAL HUB - INSTALLER                 {self.COLORS['CYAN']}║
║                                                                  ║
║  Netflix-Style Streaming Platform • Live TV • Music • Movies     ║
╚══════════════════════════════════════════════════════════════════╝{self.COLORS['END']}
"""
        print(banner)
    
    def check_internet(self):
        """Check internet connection"""
        print(f"{self.COLORS['BLUE']}[1/8]{self.COLORS['END']} Checking internet connection...")
        
        try:
            response = requests.get("https://api.github.com", timeout=5)
            if response.status_code == 200:
                print(f"{self.COLORS['GREEN']}✓ Internet connection OK{self.COLORS['END']}")
                return True
        except:
            pass
        
        print(f"{self.COLORS['RED']}✗ No internet connection{self.COLORS['END']}")
        print("  Please connect to the internet and try again.")
        return False
    
    def create_install_directory(self):
        """Create installation directory"""
        print(f"{self.COLORS['BLUE']}[2/8]{self.COLORS['END']} Preparing installation...")
        
        try:
            self.install_dir.mkdir(exist_ok=True)
            self.temp_dir.mkdir(exist_ok=True)
            print(f"{self.COLORS['GREEN']}✓ Installation directory: {self.install_dir}{self.COLORS['END']}")
            return True
        except Exception as e:
            print(f"{self.COLORS['RED']}✗ Failed to create directory: {e}{self.COLORS['END']}")
            return False
    
    def download_file(self, url, destination, filename):
        """Download a single file with progress bar"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(destination, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, 
                         desc=f"  {filename}", ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            return True
        except Exception as e:
            print(f"{self.COLORS['RED']}✗ Failed to download {filename}: {e}{self.COLORS['END']}")
            return False
    
    def download_manifest(self):
        """Download the file manifest"""
        print(f"{self.COLORS['BLUE']}[3/8]{self.COLORS['END']} Fetching file list...")
        
        manifest_url = f"{self.github_url}/contents/manifest.json"
        
        try:
            response = requests.get(manifest_url)
            if response.status_code == 200:
                self.manifest = response.json()
                
                # Decode content if it's base64 encoded
                import base64
                if "content" in self.manifest:
                    content = base64.b64decode(self.manifest["content"]).decode()
                    self.manifest = json.loads(content)
                
                print(f"{self.COLORS['GREEN']}✓ Found {len(self.manifest.get('files', {}))} files to download{self.COLORS['END']}")
                return True
        except Exception as e:
            print(f"{self.COLORS['YELLOW']}⚠ Could not fetch manifest: {e}{self.COLORS['END']}")
            print("  Using default file list...")
            # Fall back to default file list
            return True
        
        return False
    
    def download_app_files(self):
        """Download all application files"""
        print(f"{self.COLORS['BLUE']}[4/8]{self.COLORS['END']} Downloading application...")
        
        total_files = len(self.manifest.get('files', {}))
        if total_files == 0:
            print(f"{self.COLORS['YELLOW']}⚠ No files to download{self.COLORS['END']}")
            return False
        
        print(f"  Downloading {total_files} files...")
        
        successful = 0
        for filename, file_info in self.manifest.get('files', {}).items():
            # Construct download URL
            download_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/main/{filename}"
            
            destination = self.temp_dir / filename
            
            if self.download_file(download_url, destination, filename):
                # Verify file size
                if os.path.getsize(destination) == file_info.get('size', 0):
                    successful += 1
                else:
                    print(f"{self.COLORS['YELLOW']}⚠ Size mismatch for {filename}{self.COLORS['END']}")
        
        print(f"\n{self.COLORS['GREEN']}✓ Downloaded {successful}/{total_files} files{self.COLORS['END']}")
        return successful > 0
    
    def download_zip_alternative(self):
        """Alternative: Download as ZIP file"""
        print(f"{self.COLORS['BLUE']}[4/8]{self.COLORS['END']} Downloading application (ZIP)...")
        
        zip_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/archive/main.zip"
        zip_path = self.temp_dir / "app.zip"
        
        if not self.download_file(zip_url, zip_path, "Application Package"):
            return False
        
        # Extract ZIP
        print(f"{self.COLORS['BLUE']}[5/8]{self.COLORS['END']} Extracting files...")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # Move files from extracted folder
            extracted_dir = self.temp_dir / f"{self.repo_name}-main"
            if extracted_dir.exists():
                for item in extracted_dir.iterdir():
                    if item.is_file():
                        shutil.copy2(item, self.temp_dir / item.name)
                    elif item.is_dir():
                        shutil.copytree(item, self.temp_dir / item.name, dirs_exist_ok=True)
            
            print(f"{self.COLORS['GREEN']}✓ Files extracted{self.COLORS['END']}")
            return True
        except Exception as e:
            print(f"{self.COLORS['RED']}✗ Failed to extract: {e}{self.COLORS['END']}")
            return False
    
    def install_dependencies(self):
        """Install Python dependencies"""
        print(f"{self.COLORS['BLUE']}[6/8]{self.COLORS['END']} Installing dependencies...")
        
        requirements_file = self.temp_dir / "requirements.txt"
        
        if requirements_file.exists():
            try:
                import subprocess
                
                print("  Installing PyQt6 and other requirements...")
                
                # Install pip packages
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
                
                print(f"{self.COLORS['GREEN']}✓ Dependencies installed{self.COLORS['END']}")
                return True
            except Exception as e:
                print(f"{self.COLORS['YELLOW']}⚠ Could not install dependencies: {e}{self.COLORS['END']}")
                print("  You may need to install PyQt6 manually")
                return False
        else:
            # Install minimal requirements
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])
                print(f"{self.COLORS['GREEN']}✓ PyQt6 installed{self.COLORS['END']}")
                return True
            except:
                print(f"{self.COLORS['YELLOW']}⚠ Skipping dependency installation{self.COLORS['END']}")
                return False
    
    def copy_files_to_install_dir(self):
        """Copy files to final installation directory"""
        print(f"{self.COLORS['BLUE']}[7/8]{self.COLORS['END']} Installing files...")
        
        try:
            # Copy all files from temp to install dir
            for item in self.temp_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, self.install_dir / item.name)
                elif item.is_dir() and item.name != "__pycache__":
                    dest = self.install_dir / item.name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
            
            print(f"{self.COLORS['GREEN']}✓ Files installed to {self.install_dir}{self.COLORS['END']}")
            return True
        except Exception as e:
            print(f"{self.COLORS['RED']}✗ Failed to copy files: {e}{self.COLORS['END']}")
            return False
    
    def create_desktop_shortcut(self):
        """Create desktop shortcuts"""
        print(f"{self.COLORS['BLUE']}[8/8]{self.COLORS['END']} Creating shortcuts...")
        
        import platform
        system = platform.system()
        
        try:
            if system == "Windows":
                self.create_windows_shortcut()
            elif system == "Darwin":
                self.create_mac_shortcut()
            elif system == "Linux":
                self.create_linux_shortcut()
            
            print(f"{self.COLORS['GREEN']}✓ Shortcuts created{self.COLORS['END']}")
        except Exception as e:
            print(f"{self.COLORS['YELLOW']}⚠ Could not create shortcuts: {e}{self.COLORS['END']}")
    
    def create_windows_shortcut(self):
        """Create Windows shortcut"""
        import pythoncom
        from win32com.client import Dispatch
        
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "Alex's Personal Hub.lnk"
        
        wscript = Dispatch("WScript.Shell")
        shortcut = wscript.CreateShortcut(str(shortcut_path))
        
        # Create launcher script
        launcher = self.install_dir / "launch.bat"
        with open(launcher, "w") as f:
            f.write(f"""@echo off
title Alex's Personal Hub
echo Starting Alex's Personal Hub...
cd /d "{self.install_dir}"
python main_app.py
if errorlevel 1 (
    echo Failed to start application
    pause
)
""")
        
        shortcut.Targetpath = str(launcher)
        shortcut.WorkingDirectory = str(self.install_dir)
        shortcut.IconLocation = str(sys.executable)
        shortcut.save()
    
    def create_mac_shortcut(self):
        """Create macOS application"""
        app_dir = Path.home() / "Applications" / "AlexPersonalHub.app"
        contents_dir = app_dir / "Contents" / "MacOS"
        contents_dir.mkdir(parents=True, exist_ok=True)
        
        # Create launcher script
        launcher = contents_dir / "launcher"
        with open(launcher, "w") as f:
            f.write(f"""#!/bin/bash
cd "{self.install_dir}"
python3 main_app.py
""")
        
        os.chmod(launcher, 0o755)
        
        # Create Info.plist
        plist = app_dir / "Contents" / "Info.plist"
        plist.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Alex's Personal Hub</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
</dict>
</plist>""")
    
    def create_linux_shortcut(self):
        """Create Linux desktop entry"""
        desktop_entry = Path.home() / ".local" / "share" / "applications" / "alex-personal-hub.desktop"
        desktop_entry.parent.mkdir(parents=True, exist_ok=True)
        
        desktop_entry.write_text(f"""[Desktop Entry]
Name=Alex's Personal Hub
Comment=Netflix-style streaming platform
Exec=python3 {self.install_dir}/main_app.py
Path={self.install_dir}
Terminal=false
Type=Application
Categories=AudioVideo;Player;
""")
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def run(self):
        """Run the installer"""
        self.print_banner()
        
        try:
            # Step 1: Check internet
            if not self.check_internet():
                return False
            
            # Step 2: Create directories
            if not self.create_install_directory():
                return False
            
            # Step 3: Download manifest
            self.download_manifest()
            
            # Step 4: Download files
            if not self.download_zip_alternative():
                print(f"{self.COLORS['YELLOW']}Trying individual file download...{self.COLORS['END']}")
                if not self.download_app_files():
                    return False
            
            # Step 6: Install dependencies
            self.install_dependencies()
            
            # Step 7: Copy files
            if not self.copy_files_to_install_dir():
                return False
            
            # Step 8: Create shortcuts
            self.create_desktop_shortcut()
            
            # Installation complete
            print(f"\n{self.COLORS['GREEN']}{'='*70}{self.COLORS['END']}")
            print(f"{self.COLORS['YELLOW']}✨ Installation Complete! ✨{self.COLORS['END']}")
            print(f"\n{self.COLORS['GREEN']}Alex's Personal Hub has been installed to:{self.COLORS['END']}")
            print(f"  {self.COLORS['CYAN']}{self.install_dir}{self.COLORS['END']}")
            print(f"\n{self.COLORS['GREEN']}To start the application:{self.COLORS['END']}")
            print(f"  1. Look for the desktop shortcut")
            print(f"  2. Or run: cd \"{self.install_dir}\" && python main_app.py")
            
            # Launch application?
            print(f"\n{self.COLORS['YELLOW']}Launch application now? (Y/N): {self.COLORS['END']}", end="")
            choice = input().strip().upper()
            
            if choice == 'Y':
                print(f"\n{self.COLORS['BLUE']}Launching...{self.COLORS['END']}")
                os.chdir(self.install_dir)
                os.system(f"{sys.executable} main_app.py")
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n{self.COLORS['YELLOW']}Installation cancelled.{self.COLORS['END']}")
            return False
        except Exception as e:
            print(f"\n{self.COLORS['RED']}Installation failed: {e}{self.COLORS['END']}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    installer = AppInstaller()
    
    # Make sure we have required packages
    try:
        import requests
        from tqdm import tqdm
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "tqdm"])
    
    success = installer.run()
    
    if not success:
        print(f"\n{installer.COLORS['RED']}Installation failed. Please check your internet connection and try again.{installer.COLORS['END']}")
        input("Press Enter to exit...")
        sys.exit(1)
