from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from pydantic import BaseModel, Field
from datetime import datetime
import traceback
import os
import re
from pathlib import Path
import logging
import sys
import importlib.util
#from ssh_executor import RemoteExecutorTool
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
# 🚀 YAML Update Tool
# ----------------------------------------------------------
@tool(permission=ToolPermission.READ_WRITE)
def update_deployment_yaml(artifact: Artifact):
    """
    Downloads remote Kubernetes YAML, updates image references,
    replaces variable placeholders, uploads back, and commits via Git.
    """
    try:
        # Import RemoteExecutorTool dynamically
        ssh_module = import_latest_module("ssh_executor.py", "ssh_executor")
        RemoteExecutorTool = ssh_module.RemoteExecutorTool
        executor = RemoteExecutorTool()

        # Logging
        logger = logging.getLogger("update_deployment_yaml")
        logging.basicConfig(level=logging.INFO)

        # Load environment variables
        remote_yaml_dir = os.getenv("yaml_dir")
        remote_repo_path = os.getenv("repo_path")
        variables = {
            "APP_NAMESPACE": os.environ['namespace'],
            "APP_HOST": os.environ['server'],
            "LOAD_NAMESPACE": "load1",
            "enableInstana": "true",
        }

        # Local temporary YAML path
        local_temp_dir = Path("/tmp/yaml_edit")
        local_temp_dir.mkdir(exist_ok=True)
        local_yaml_path = local_temp_dir / "deployment.yaml"

        # Remote YAML path
        remote_yaml_path = f"{remote_yaml_dir}/{artifact.affected_service.rsplit('-',1)[0].replace('-', '_')}.yaml"
        logger.info(f"⬇️ Downloading YAML from {remote_yaml_path}...")
        executor.download_file(remote_yaml_path, str(local_yaml_path))
        logger.info(f"✅ YAML downloaded to {local_yaml_path}")

        # Update image in YAML
        content = local_yaml_path.read_text()
        updated_content, count = re.subn(
            r'(?m)^(.*image:\s*)(\S+)',
            rf'\1{artifact.image_full}',
            content
        )

        updated_content, count = re.subn(
            r'(?m)^(.*namespace:\s*)(\S+)',
            rf'\1{os.environ['namespace']}',
            updated_content
        )
        # Replace variable placeholders
        for key, value in variables.items():
            pattern1 = r"{{\s*\.?Values\.?" + re.escape(key) + r"\s*}}"
            pattern2 = r"{{\s*" + re.escape(key) + r"\s*}}"
            updated_content = re.sub(pattern1, value, updated_content)
            updated_content = re.sub(pattern2, value, updated_content)

        if count == 0:
            logger.info("⚠️ No 'image:' lines found to update.")
        else:
            local_yaml_path.write_text(updated_content)
            logger.info(f"✅ Updated {count} image reference(s) to {artifact.image_full}")

        # Upload updated YAML back
        logger.info(f"📤 Uploading updated YAML to {remote_yaml_path}...")
        executor.upload_content(local_yaml_path.read_text(), remote_yaml_path)
        logger.info("✅ Upload complete.")

        # Git commit & push remotely
        commit_msg = f"update deployment image to {artifact.image_full}"
        git_cmds = [
            f"cd {remote_repo_path}",
            "git add .",
            f"git commit -m '{commit_msg}' || echo 'ℹ️ No changes to commit'",
            "git push || echo '⚠️ Push skipped or failed'"
        ]
        full_cmd = " && ".join(git_cmds)
        logger.info("🚀 Running Git commit and push remotely...")
        result = executor.run_command(full_cmd)
        logger.info("📜 Git Output:")
        logger.info(result.output if hasattr(result, "output") else result)

        return {"status": "success", "updated_image": artifact.image_full, "remote_yaml": remote_yaml_path}

    except Exception as e:
        tb = traceback.format_exc()
        return {"status": "error", "error": str(e), "traceback": tb}

