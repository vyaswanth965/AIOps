from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from pydantic import BaseModel, Field
from datetime import datetime
import traceback
import os
import sys
import importlib.util

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
# ⚙️ Dynamic import
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
# 🧱 Artifact Pydantic Model
# ----------------------------------------------------------
class Artifact(BaseModel):
    affected_service: str
    image_full: str

# ----------------------------------------------------------
# 🚀 Deployment Tool
# ----------------------------------------------------------
@tool(permission=ToolPermission.READ_WRITE)
def deploy_image(artifact: Artifact):
    """
    Deploy affected service YAML using Terraform & OC login
    inside Watsonx Orchestrate runtime.
    """
    try:
        # Import latest modules
        ssh_module = import_latest_module("ssh_executor.py", "ssh_executor")
        RemoteExecutorTool = ssh_module.RemoteExecutorTool

        # Initialize SSH executor
        ssh_tool = RemoteExecutorTool()

        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        REMOTE_DIR = os.environ['remote_dir']
        REMOTE_YAML_DIR = os.environ['yaml_dir']
        OC_SERVER = os.environ['server']
        OC_TOKEN = os.environ['token']
        OC_PROJECT = os.environ['namespace']
        QUAY_REGISTRY = "quay.io"
        QUAY_USER = os.environ['username']
        QUAY_PASSWORD = os.environ['password']

        # Determine remote YAML path
        remote_yaml_file = f"{REMOTE_YAML_DIR}/{artifact.affected_service.rsplit('-',1)[0].replace('-','_')}.yaml"

        # Terraform main.tf content
        terraform_content = f"""
terraform {{
  required_providers {{
    kubectl = {{
      source  = "gavinbunney/kubectl"
      version = ">= 1.14.0"
    }}
  }}
}}

provider "kubectl" {{
  config_path       = "~/.kube/config"
  load_config_file  = true
  apply_retry_count = 3
}}

locals {{
  yaml_path = "{remote_yaml_file}"
}}

resource "kubectl_manifest" "qotd" {{
  yaml_body = file(local.yaml_path)
}}
"""

        # Upload Terraform config to remote
        ssh_tool.run_command(f"mkdir -p {REMOTE_DIR}")
        ssh_tool.run_command(f"cd {REMOTE_DIR} && rm -f main.tf terraform.tfstate || echo '⚠️ Files not found or already deleted'")


        ssh_tool.upload_content(terraform_content,f"{REMOTE_DIR}/main.tf")

        # Commands to execute
        commands = [
            f"oc login {OC_SERVER} --token={OC_TOKEN} --insecure-skip-tls-verify=true",
            f"oc project {OC_PROJECT}",
            f"podman login {QUAY_REGISTRY} -u {QUAY_USER} -p {QUAY_PASSWORD}",
            f"cd {REMOTE_DIR} && terraform init -input=false",
            f"cd {REMOTE_DIR} && terraform apply -auto-approve -input=false"
        ]

        results = []
        for cmd in commands:
            output = ssh_tool.run_command(cmd)
            results.append({"command": cmd, "output": output})

        return {
            "status": "success",
            "image_full": artifact.image_full,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        tb = traceback.format_exc()
        return {
            "status": "error",
            "error": str(e),
            "traceback": tb,
        }
