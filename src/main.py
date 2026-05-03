#!/usr/bin/env python3
"""
IBM-Bob Chat Application - Main Launcher
Starts both the chat server and client application
"""

import os
import sys
import subprocess
import time
import signal
import platform
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

class ChatAppLauncher:
    def __init__(self):
        self.processes = []
        self.server_process = None
        self.client_process = None
        
    def check_environment(self):
        """Check if .env file exists"""
        env_file = Path('.env')
        if not env_file.exists():
            print("⚠️  Warning: .env file not found!")
            print("📝 Creating .env from template...")
            
            template = Path('config/.env.example')
            if template.exists():
                import shutil
                shutil.copy(template, env_file)
                print("✅ .env file created. Please edit it with your credentials.")
                print("   Required: WATSONX_API_KEY, WATSONX_PROJECT_ID")
                return False
            else:
                print("❌ Error: config/.env.example not found!")
                return False
        return True
    
    def check_certificates(self):
        """Check if SSL certificates exist"""
        cert_file = Path('certs/server.crt')
        key_file = Path('certs/server.key')
        
        if not cert_file.exists() or not key_file.exists():
            print("⚠️  SSL certificates not found!")
            print("🔐 Generating certificates...")
            
            script = Path('scripts/generate_certs.sh')
            if script.exists():
                if platform.system() == 'Windows':
                    print("❌ Please run: bash scripts/generate_certs.sh")
                    return False
                else:
                    subprocess.run(['bash', str(script)], check=True)
                    print("✅ Certificates generated!")
            else:
                print("❌ Error: scripts/generate_certs.sh not found!")
                return False
        return True
    
    def start_server(self):
        """Start the chat server"""
        print("\n🖥️  Starting Chat Server...")
        server_script = Path('src/server/chat_server.py')
        
        if not server_script.exists():
            print(f"❌ Error: {server_script} not found!")
            return False
        
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, str(server_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.processes.append(self.server_process)
            
            # Wait a bit for server to start
            time.sleep(2)
            
            if self.server_process.poll() is None:
                print("✅ Chat Server started successfully!")
                return True
            else:
                print("❌ Chat Server failed to start!")
                return False
                
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def start_client(self):
        """Start the Flet client"""
        print("\n📱 Starting Flet Client...")
        client_script = Path('src/client/flet_app.py')
        
        if not client_script.exists():
            print(f"❌ Error: {client_script} not found!")
            return False
        
        try:
            self.client_process = subprocess.Popen(
                [sys.executable, str(client_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.processes.append(self.client_process)
            
            print("✅ Flet Client started successfully!")
            print("\n🌐 Application should open in your browser shortly...")
            print("   If not, check the output above for the URL")
            return True
                
        except Exception as e:
            print(f"❌ Error starting client: {e}")
            return False
    
    def cleanup(self, signum=None, frame=None):
        """Clean up processes on exit"""
        print("\n\n🛑 Shutting down...")
        
        for process in self.processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                except Exception as e:
                    print(f"⚠️  Error stopping process: {e}")
        
        print("✅ All processes stopped.")
        sys.exit(0)
    
    def run(self):
        """Main run method"""
        print("=" * 60)
        print("🤖 IBM-Bob Chat Application Launcher")
        print("=" * 60)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        # Check prerequisites
        print("\n📋 Checking prerequisites...")
        
        if not self.check_environment():
            print("\n❌ Setup incomplete. Please configure .env file and try again.")
            return 1
        
        if not self.check_certificates():
            print("\n❌ Setup incomplete. Please generate certificates and try again.")
            return 1
        
        print("✅ All prerequisites met!")
        
        # Start components
        if not self.start_server():
            print("\n❌ Failed to start server. Check the error messages above.")
            self.cleanup()
            return 1
        
        if not self.start_client():
            print("\n❌ Failed to start client. Check the error messages above.")
            self.cleanup()
            return 1
        
        # Keep running
        print("\n" + "=" * 60)
        print("✅ Application is running!")
        print("=" * 60)
        print("\n📝 Press Ctrl+C to stop all services\n")
        
        try:
            # Monitor processes
            while True:
                time.sleep(1)
                
                # Check if server is still running
                if self.server_process and self.server_process.poll() is not None:
                    print("\n⚠️  Server process stopped unexpectedly!")
                    break
                
                # Check if client is still running
                if self.client_process and self.client_process.poll() is not None:
                    print("\n⚠️  Client process stopped unexpectedly!")
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
        
        return 0


def main():
    """Entry point"""
    launcher = ChatAppLauncher()
    return launcher.run()


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
