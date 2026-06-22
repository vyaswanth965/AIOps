# src/tools/ssh_executor.py
"""
SSH Remote Execution Tool
Handles command execution on the Ubuntu control VM
"""

import paramiko
import os
import structlog
from typing import Dict, Tuple, Optional, List
from pathlib import Path
import tempfile
import time

logger = structlog.get_logger()
from dotenv import load_dotenv
import os
load_dotenv()
import io
import base64

class SSHExecutor:
    """Execute commands on remote Ubuntu VM via SSH"""
    
    def __init__(self, host: str, username: str, password: Optional[str] = None,
                 key_path: Optional[str] = None, port: int = 22):
        """
        Initialize SSH executor
        
        Args:
            host: Hostname or IP of the Ubuntu VM
            username: SSH username
            password: SSH password (optional if using key)
            key_path: Path to SSH private key (optional if using password)
            port: SSH port (default 22)
        """
        self.host = host
        self.username = username
        self.password = password
        self.key_path = key_path
        self.port = port
        self.client = None
        self.sftp = None
        
    def connect(self) -> None:
        """Establish SSH connection"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
            }
            

            b64_key = os.getenv("key_str")
            if b64_key:
                decoded = base64.b64decode(b64_key).decode("utf-8")
                key = paramiko.RSAKey.from_private_key(io.StringIO(decoded))
                connect_kwargs["pkey"] = key

            # if self.key_path:
                # # Expand ~ to home directory
                # key_path_expanded = os.path.expanduser(self.key_path)
                # # print('**********************')
                # # print(key_path_expanded)
                # # print('********************')



                # key = paramiko.RSAKey.from_private_key_file(key_path_expanded)
                # connect_kwargs["pkey"] = key
            elif self.password:
                connect_kwargs["password"] = self.password
            else:
                raise ValueError("Either password or key_path must be provided")
            
            print(connect_kwargs)
            
            self.client.connect(**connect_kwargs)
            self.sftp = self.client.open_sftp()
            logger.info("SSH connection established", host=self.host)
            
        except Exception as e:
            logger.error("Failed to connect via SSH", host=self.host, error=str(e))
            raise
    
    def disconnect(self) -> None:
        """Close SSH connection"""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        logger.info("SSH connection closed", host=self.host)
    
    def execute_command(self, command: str, timeout: int = 300) -> Tuple[int, str, str]:
        """
        Execute a command on the remote host
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if not self.client:
            self.connect()
        
        try:
            logger.info("Executing remote command", command=command[:100])
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            # Wait for command to complete
            exit_code = stdout.channel.recv_exit_status()
            
            # Read output
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            
            logger.info("Command executed", 
                       command=command[:100], 
                       exit_code=exit_code)
            
            return exit_code, stdout_data, stderr_data
            
        except Exception as e:
            logger.error("Command execution failed", command=command, error=str(e))
            raise
    
    def upload_file(self, local_path: str, remote_path: str) -> None:
        """Upload a file to the remote host"""
        if not self.sftp:
            self.connect()
        
        try:
            # Expand ~ in remote path
            if remote_path.startswith('~'):
                remote_path = remote_path.replace('~', '/home/' + self.username, 1)
            
            # Ensure remote directory exists
            remote_dir = os.path.dirname(remote_path)
            self.execute_command(f"mkdir -p {remote_dir}")
            
            self.sftp.put(local_path, remote_path)
            logger.info("File uploaded", 
                       local_path=local_path, 
                       remote_path=remote_path)
            
        except Exception as e:
            logger.error("File upload failed", 
                        local_path=local_path,
                        remote_path=remote_path,
                        error=str(e))
            raise
    
    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download a file from the remote host"""
        if not self.sftp:
            self.connect()
        
        try:
            # Ensure local directory exists
            local_dir = os.path.dirname(local_path)
            os.makedirs(local_dir, exist_ok=True)
            
            self.sftp.get(remote_path, local_path)
            logger.info("File downloaded",
                       remote_path=remote_path,
                       local_path=local_path)
            
        except Exception as e:
            logger.error("File download failed",
                        remote_path=remote_path,
                        local_path=local_path,
                        error=str(e))
            raise
    
    def create_remote_file(self, remote_path: str, content: str) -> None:
        """Create a file on the remote host with the given content"""
        # Create temp file with delete=False to prevent premature deletion
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Upload the file
            self.upload_file(tmp_path, remote_path)
            
            # Make executable if it's a shell script
            if remote_path.endswith('.sh'):
                self.execute_command(f"chmod +x {remote_path}")
        finally:
            # Clean up temp file after upload
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def setup_workspace(self, base_path: str = "~/ITOps") -> None:
        """Setup the workspace structure on the remote VM"""
        commands = [
            f"mkdir -p {base_path}/packer",
            f"mkdir -p {base_path}/terraform", 
            f"mkdir -p {base_path}/scripts",
            f"mkdir -p {base_path}/output",
            f"mkdir -p {base_path}/openshift",
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.execute_command(cmd)
            if exit_code != 0:
                raise RuntimeError(f"Failed to create directory: {stderr}")
        
        logger.info("Remote workspace setup complete", base_path=base_path)
    
    def check_tool_availability(self) -> Dict[str, bool]:
        """Check if required tools are available on the remote VM"""
        tools = {
            "podman": "podman --version",
            "packer": "packer version",
            "terraform": "terraform version",
            "oc": "oc version",
            "jq": "jq --version"
        }
        
        availability = {}
        for tool, check_cmd in tools.items():
            exit_code, _, _ = self.execute_command(f"which {tool.split()[0]}")
            availability[tool] = exit_code == 0
            
        logger.info("Tool availability check", tools=availability)
        return availability


class RemoteExecutorTool:
    """LangChain tool wrapper for SSH executor"""
    
    def __init__(self):
        """Initialize with SSH configuration"""
        self.executor = SSHExecutor(
            host=os.environ['host'],
            username=os.environ['user'],
            password=os.environ['password'],
            port=os.environ["port"]
        )
        self.executor.connect()
    
    def run_command(self, command: str) -> Dict[str, any]:
        """Execute a command and return structured result"""
        try:
            exit_code, stdout, stderr = self.executor.execute_command(command)
            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command
            }
    
    def upload_content(self, content: str, remote_path: str) -> Dict[str, any]:
        """Upload content as a file to remote VM"""
        try:
            self.executor.create_remote_file(remote_path, content)
            return {
                "success": True,
                "remote_path": remote_path,
                "message": f"File created at {remote_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "remote_path": remote_path
            }
        
    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download a file from the remote host"""
        try: 
            self.executor.download_file(remote_path, local_path)
            return {
                "success": True,
                "remote_path": remote_path,
                "message": f"File downloaded at {local_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "remote_path": remote_path
            }

    # def __del__(self):
    #     """Cleanup connection on deletion"""
    #     if hasattr(self, 'executor'):
    #         try:
    #             self.executor.disconnect()
    #         except:
    #             pass