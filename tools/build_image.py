from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from pydantic import BaseModel, Field
from datetime import datetime
import traceback
import os
import sys
import importlib.util
import logging
from typing import Dict, Any
from ssh_executor import RemoteExecutorTool
from generate_packer_config import generate_packer_config

# ----------------------------------------------------------
# 🔍 Utility to find latest tool directory
# ----------------------------------------------------------
def find_latest_tool_directory(tool_file_name: str) -> str:
    tool_root = "/shared"
    latest_dir = None
    latest_time = 0
    for entry in os.listdir(tool_root):
        sub_dir = os.path.join(tool_root, entry)
        if not os.path.isdir(sub_dir):
            continue
        tool_path = os.path.join(sub_dir, tool_file_name)
        if os.path.exists(tool_path):
            mtime = os.path.getmtime(tool_path)
            if mtime > latest_time:
                latest_time = mtime
                latest_dir = sub_dir
    if not latest_dir:
        raise FileNotFoundError(f"{tool_file_name} not found in /shared")
    return latest_dir

# ----------------------------------------------------------
# ⚙️ Dynamic import helper
# ----------------------------------------------------------
def import_latest_module(file_name: str, module_name: str):
    latest_dir = find_latest_tool_directory(file_name)
    file_path = os.path.join(latest_dir, file_name)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module

# ----------------------------------------------------------
# 🧱 Alert Model
# ----------------------------------------------------------
class Alert(BaseModel):
    alert_id: str
    cve_id: str
    severity: str
    affected_service: str
    affected_image: str
    description: str
    remediation: str
    detected_at: str
    source: str

# ----------------------------------------------------------
# 🏗️ ADK Tool — Build Image with Packer
# ----------------------------------------------------------
@tool(permission=ToolPermission.READ_WRITE)
def build_image(alert: Alert):
    """
    Builds a remediated container image remotely using Packer.
    Generates and uploads a Packer configuration before build.
    Returns full image metadata after successful build.
    """
    try:
        print('in')
        logger = logging.getLogger("build_image")
        logging.basicConfig(level=logging.INFO)

        # 🔄 Import latest dependencies dynamically
        # ssh_module = import_latest_module("ssh_executor.py", "ssh_executor")
        # packer_module = import_latest_module("generate_packer_config.py", "generate_packer_config")

        # RemoteExecutorTool = ssh_module.RemoteExecutorTool
        # generate_packer_config = packer_module.generate_packer_config

        executor = RemoteExecutorTool()

        # ✅ Handle if alert is already a dict
        if isinstance(alert, BaseModel):
            #alert_data = alert.dict()       # For Pydantic v1
            alert_data = alert.model_dump()  # For Pydantic v2
        elif isinstance(alert, dict):
            alert_data = alert
        else:
            raise TypeError(f"Invalid alert type: {type(alert)}")
        
        # 🧩 Generate and upload Packer config
        image_tag = generate_packer_config(alert_data)

        logger.info(f"🧱 Generated packer config with image tag: {image_tag}")

        # 🔐 Load registry environment details
        registry = os.environ['registry']
        username = os.environ['username']
        repository = os.environ['repository']

        # 🧰 Initialize and build image remotely
        logger.info("🚀 Running remote Packer build...")
        executor.run_command(f"cd {os.environ['workspace_path']}/packer && packer init .")

        status = executor.run_command(
            f"cd {os.environ['workspace_path']}/packer && packer build "
            f"-var registry={registry} "
            f"-var registry_username={username} "
            f"-var repository_name={repository} remediation.pkr.hcl"
        )

        # 🧾 Handle result
        if isinstance(status, dict) and status.get("exit_code", 1) == 0:
            image_full = f"{registry}/{username}/{repository}:{image_tag}"
            artifact = {
                "image_full": image_full,
                "registry": registry,
                "repository": repository,
                "tag": image_tag,
                "affected_service": alert_data.get("affected_service"),
                "built_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"✅ Successfully built remote image: {image_full}")
            return {"status": "success", "artifact": artifact}
        else:
            logger.error("❌ Packer build failed")
            return {"status": "failed", "error": status}

    except Exception as e:
        tb = traceback.format_exc()
        return {"status": "error", "error": str(e), "traceback": tb}
    
if __name__=='__main__':
    r=build_image(Alert(alert_id= 'ALERT-2025-001', cve_id= 'CVE-2022-2068', severity= 'high', affected_service= 'qotd-ratings-service', affected_image= 'registry.gitlab.com/quote-of-the-day/qotd-ratings-service:v5.1.0', description= 'OpenSSL vulnerability affecting Alpine Linux base image. The c_rehash script does not properly sanitise shell metacharacters to prevent command injection.', remediation= 'Update OpenSSL package to latest version and rebuild container image', detected_at= '2025-10-27T07:13:21.871775', source= 'Concert Security Scanner')   ) 
    #r=build_image({'alert_id': 'ALERT-2025-001', 'cve_id': 'CVE-2022-2068', 'severity': 'high', 'affected_service': 'qotd-ratings-service', 'affected_image': 'registry.gitlab.com/quote-of-the-day/qotd-ratings-service:v5.1.0', 'description': 'OpenSSL vulnerability affecting Alpine Linux base image. The c_rehash script does not properly sanitise shell metacharacters to prevent command injection.', 'remediation': 'Update OpenSSL package to latest version and rebuild container image', 'detected_at': '2025-10-27T07:13:21.871775', 'source': 'Concert Security Scanner'})    
    print(r)