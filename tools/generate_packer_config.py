# src/agents/generate_packer_config.py
import os
import time
import json
import logging
from typing import Dict, Any, List
from jinja2 import Template
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ibm import ChatWatsonx
from ssh_executor import RemoteExecutorTool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# PACKER TEMPLATE
# ---------------------------------------------------------------------
PACKER_TEMPLATE = """
packer {
  required_plugins {
    docker = {
      source  = "github.com/hashicorp/docker"
      version = ">= 1.0.0"
    }
  }
}

variable "registry" {
  type    = string
  default = "{{ registry }}"
}

variable "registry_username" {
  type    = string
  default = "{{ registry_username }}"
}

variable "repository_name" {
  type    = string
  default = "{{ repository_name }}"
}

variable "base_image" {
  type    = string
  default = "{{ base_image }}"
}

source "docker" "{{ source_name }}" {
  image  = "{{ base_image }}"
  commit = true
  pull   = true
}

build {
  name    = "{{ build_name }}"
  sources = ["source.docker.{{ source_name }}"]
  
  provisioner "shell" {
    inline = [
      {{ shell_commands }}
    ]
  }
  
  post-processor "docker-tag" {
    repository = "${var.registry}/${var.registry_username}/${var.repository_name}"
    tags       = ["{{ cve_tag }}"]
  }
}
"""

SYSTEM_PROMPT = """You are a DevOps automation expert specializing in:
- Packer for building container images
- Security remediation and CVE patching
- Linux OS hardening and image cleanup

Instructions:
When generating Packer templates (e.g., in HCL or JSON), always ensure that shell or inline commands used in provisioners are safe, syntactically correct, and non-destructive.

Allowed Commands:

Standard package management and update commands, such as:
apk update
apk upgrade
apk add --no-cache [package]
apk del --purge [package]

Safe cleanup operations:
rm -rf /var/cache/apk/*

Informational or verification commands (e.g., apk info, cat /etc/os-release, echo "Done").

Not Allowed Commands:

Any destructive or system-wide cleanup like:
find / -exec rm
rm -rf /*
Commands that modify /proc, /sys, /dev, /run, /etc/passwd, etc.
Any apk command using version operators such as <, >, <=, >=, or =.
File redirections (<, >, >>) that might overwrite files.


Return ONLY a JSON array of shell commands (strings) needed to remediate the CVE. avoid find command.
"""

# ---------------------------------------------------------------------
# LLM HELPERS
# ---------------------------------------------------------------------
def extract_json_array(content: str) -> List[str]:
    """Safely extract a JSON array from LLM output or return fallback commands."""
    try:
        start, end = content.find("["), content.rfind("]") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            if isinstance(parsed, list):
                return parsed
    except Exception:
        pass
    # fallback if malformed or empty
    return [
        "apk update",
        "apk upgrade --no-cache",
        "apk add --no-cache ca-certificates openssl curl bash",
        "rm -rf /var/cache/apk/*",
        "echo 'remediation complete'"
    ]


def create_llm_client() -> ChatWatsonx:
    """Initialize ChatWatsonx LLM from environment variables."""
    params = {
        "decoding_method": "greedy",
        "max_new_tokens": 3000,
        "min_new_tokens": 1,
    }
    return ChatWatsonx(
        model_id=os.environ["model_id"],
        project_id=os.environ["project_id"],
        apikey=os.environ["apikey"],
        url=os.environ["url"],
        params=params
    )


def ask_llm_for_commands(llm_client: ChatWatsonx, alert: Dict[str, Any]) -> List[str]:
    """Ask the LLM to generate remediation commands."""
    human_msg = HumanMessage(content=f"""
Generate shell commands to remediate this vulnerability.

CVE ID: {alert.get('cve_id')}
Severity: {alert.get('severity')}
Affected Image: {alert.get('affected_image')}
Service: {alert.get('affected_service')}
Description: {alert.get('description')}
Remediation: {alert.get('remediation')}

Return only JSON array, e.g.:
["command1", "command2", "command3"]
""")
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    try:
        response = llm_client.invoke([system_msg, human_msg])
        content = getattr(response, "content", "") or str(response)
        commands = extract_json_array(content)
    except Exception as e:
        logger.warning("⚠️ LLM generation failed, using fallback: %s", e)
        commands = extract_json_array("")
    return commands

# ---------------------------------------------------------------------
# PACKER RENDERING
# ---------------------------------------------------------------------
def render_packer_config(alert: Dict[str, Any], commands: List[str]) -> (str, str):
    """Render packer template dynamically using LLM-generated commands."""
    tag_suffix = (alert.get("cve_id") or "patch").lower().replace("-", "")
    unique_tag = f"{int(time.time())}-{tag_suffix}"

    params = {
        "registry": os.environ["registry"],
        "registry_username": os.environ["username"],
        "repository_name": os.environ["repository"],
        "base_image": alert.get("affected_image", "alpine:latest"),
        "source_name": "patched_source",
        "build_name": f"cve_{tag_suffix}",
        "shell_commands": ",\n      ".join([json.dumps(cmd) for cmd in commands]),
        "cve_tag": unique_tag,
    }

    packer_config = Template(PACKER_TEMPLATE).render(**params)
    return packer_config, unique_tag

# ---------------------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------------------
def generate_packer_config(alert: Dict[str, Any], workspace: str = os.environ['workspace_path']+'/packer') -> str:
    """Generate packer config dynamically using LLM and upload to remote VM."""
    llm = create_llm_client()
    commands = ask_llm_for_commands(llm, alert)
    packer_content, unique_tag = render_packer_config(alert, commands)

    remote = RemoteExecutorTool()
    
    remote.upload_content(packer_content, f"{workspace}/remediation.pkr.hcl")

    logger.info("✅ Uploaded LLM-generated packer config with tag %s", unique_tag)
    return unique_tag