# 2 - Agent Creation 🤖

> Learn how to define and configure agents using provided YAML and Python files. This step sets the foundation for building intelligent, task-specific agents that power your automation flow.

---

ℹ️ As a reminder here are the agents that we are leveraging for this project:

<p align="center">
  <img src="images/distributed_agents.png" width=800px />
</p>

The sequence diagram below demonstrates interactions between the components in this lab:

<p align="center">
  <img src="images/distributed_agent_flow.svg" width=800px />
</p>

---

### Table of Contents

- [Step 1 – Import Agents &amp; Tools](#step-1--import-agents-&-tools)
- [Step 2 – Concert Agent with ADK](#step-2--concert-agent-with-adk)
- [Step 3 – Jenkins Agent](#step-3--jenkins-agent)
- [Step 4 – Packer Agent](#step-4--packer-agent)
- [Step 5 – Terraform Agent](#step-5--terraform-agent)
- [Step 6 - Supervisor Agent](#step-6--supervisor-agent)

---

## Step 0 - Set Up & Configuration

1. 🚨Ensure you have completed the pre-requisites --> [Find them here](https://github.com/aishwarya-hariharan/ibm-agentic-ai-for-itops/blob/main/pre-requisties/Hands%20on%20Lab%20Pre-Requisites%20-%20Set%20Up%20%26%20Configuration.md#4--create-and-activate-a-virtual-environment)
   
2. Clone the Repository

Open VS Code Terminal and Run below command

```bash
git clone https://github.ibm.com/ibm-us-fsm-ce/agentic-ai-for-itopsops.git
```

3. Navigate into the Project Folder

```bash
cd agentic-ai-for-itopsops/Distributed_Platforms
```
---

## Step 1 – Import Agents & Tools

> 🚨 By this point, you should have the project structure available on your local machine in the /agentic-ai-for-itops directory.

### Configure Environment Variables

Before importing tools and agents, you need to configure the required environment variables.

Navigate to the `.env` file located in:
`/agentic-ai-for-itopsops/Distributed_Platforms/tools`

> The `.env` file stores configuration values used by the import.sh script for authentication, environment setup, and orchestrating imports.

Below are the required fields organized by category. **➡️ Your lab instructor will provide instructions on how to obtain the necessary values for these variables.**

Below are the required fields with brief descriptions:

```env
############################################
# Remote Host Configuration
############################################
host=your_remote_host_or_ip                      # SSH host or VM IP (e.g., 10.0.0.10)
user=your_ssh_username                           # SSH username (e.g., ubuntu, root)
port=your_ssh_port                               # SSH port (e.g., 22)
workspace_path=/root/ITOps                             # Workspace folder on remote machine

# Base64-encoded private key (OpenSSH PEM → base64)
# Python: import base64; print(base64.b64encode(open("key.pem","rb").read()).decode())
# macOS/Linux:  base64 key.pem | tr -d '\n'
# WinPS:  [Convert]::ToBase64String([IO.File]::ReadAllBytes("key.pem"))
key_str=your_base64_encoded_ssh_key_here


############################################
# Elasticsearch Configuration
############################################
ELASTICSEARCH_FULL_URL=https://your-es-host:your_port     # Full ES URL
ELASTICSEARCH_HOST=https://your-es-host                   # ES host (without port)
ELASTICSEARCH_PORT=your_es_port                           # ES port
ELASTIC_USER=your_elasticsearch_username                  # Elasticsearch username
ELASTIC_PASSWORD=your_elasticsearch_password              # Elasticsearch password


############################################
# Model Configuration (LLM / WatsonX)
############################################
model_id=meta-llama/llama-3-405b-instruct                 # Model to use
project_id=ee53e355-6cb4-4372-8240-9f6684179706           # IBM WatsonX project ID
apikey=api_key of the ibm account hosting llm model       # IBM Cloud / WatsonX API key
url=https://us-south.ml.cloud.ibm.com                     # WatsonX API endpoint


############################################
# Repository & Directory Paths
############################################
yaml_dir=/root/qotd_test_v01/resources/k8s/ocp_okd/v4.0.0   # Kubernetes YAML directory
repo_path=/root/qotd_test_v01                             # Repository path on remote VM
remote_dir=/root/IT/terraform                          # Terraform directory on remote VM



############################################
# quay.io Container Registry Credentials
############################################
registry=quay.io                                          # Registry ( quay.io)
username=your_registry_username                           # Registry username
password=your_registry_password_or_token                  # Registry password / token
repository=your_container_repository_name                 # Image repo name (e.g., org/app)


############################################
# OpenShift Configuration
############################################
server=https://your-openshift-api-server:your_api_port    # OpenShift API endpoint
token=your_openshift_access_token                         # Cluster access token
namespace=your_k8s_namespace                              # Deployment namespace/project

```

---

### Edit the Environment File

To configure your environment:

- Open the .env file using a plain text editor (e.g., VS Code, Sublime Text, nano, or vi).
- Update each variable with the appropriate values. _❗Consult your lab instructor for guidance on obtaining these values._
- Save and close the file.

---

### Understanding the Import Script

Navigate back to the `/agentic-ai-for-itops/Distributed_Platforms` directory. This directory contains the `import-all.sh_ script`

The `import-all.sh` script automates the setup and import process for the watsonx Orchestrate platform. It handles the configuration of environment variables, connections, Python tools, knowledge bases, and agents, importing them from your local machine to your watsonx Orchestrate instance.

---

### What Gets Imported

#### Tools 🧰

Located in `/agentic-ai-for-itops/Distributed_Platforms/tools`, the following Python utilities will be registered with Orchestrate:

- `build_image.py` – Builds container images for deployment
- `update_deployment_yaml.py` – Updates deployment YAML configurations dynamically
- `deploy_image.py` – Deploys container images to the target environment
- `generate_packer_config.py` – Generates HashiCorp Packer configuration files

> Note: You will create additional custom agent tools and import them in the next section.

#### Knowledge Bases 📂

Located in `/agentic-ai-for-itops/Distributed_Platforms/knowledge_base/`

> Note: You will create your agent knowledge base and import it in the next section.

#### Agents 🤖

Located in `/agentic-ai-for-itops/Distributed_Platforms/agents`, each `YAML` file defines the behavior and configuration for an orchestration agent:

- `supervisor.yaml`– Oversees and coordinates the execution of other agents
- `packer.yaml` – Automates container image building using HashiCorp Packer
- `terraform.yaml` – Manages infrastructure provisioning and configuration with Terraform

---

🚨 Make sure you have an active env; watsonx Orchestrate token expire every an hour for security reasons 🚨

Use this command with your enviornment name and api key: 

```
orchestrate env activate <environment-name> --api-key <your-api-key>
```

---

#### Install Python Dependencies

Before running the import script, install the required Python dependencies by running:
`pip install -r tools/requirements.txt`

---

### Execute the Import ⤵️

The `import-all.sh script` is located in: <br>
`/agentic-ai-for-itops/Distributed_Platforms`

Before executing the script, **ensure you have configured the `.env` file as described above.** Then follow the following steps:

1. Navigate to the directory:
   `cd /agentic-ai-for-itopsops/Distributed_Platforms`
2. Make the script executable:
   `chmod +x import-all.sh`
3. Execute the import script:
   `./import-all.sh`

ℹ️ The script will process the configuration and import all tools, knowledge bases, and agents to your watsonx Orchestrate platform.

Monitor the terminal output for progress updates, completion messages, and any potential errors that may require attention.

> NOTE: If you see the following error you may ignore it and proceed
> <p align="center">
  <img src="images/error.png" width=800px />
</p>

---

<p align="center"> ✨Now let's start the process of creating an agent with ADK!🤖✨</p>

---

## Step 2 – Concert Agent with ADK

---

### Building a Custom security Agent to Interact with IBM Concert! 💻

[IBM Concert](https://www.ibm.com/products/concert) is a comprehensive AI-powered platform for IT operations that includes built-in agentic AI capabilities.

> Concert 2.0 natively provides intelligent automation for security risk management, compliance monitoring, and operational resilience across hybrid cloud environments. The platform's embedded agents can autonomously detect vulnerabilities, correlate incidents, and orchestrate remediation workflows without requiring custom development.

---

In this lab, the **"Concert Agent"** we are building with the ADK is not replacing Concert's native intelligence. Instead, we are building a specialized adapter (or "specialized agent" ) that allows our central Supervisor to communicate with the Concert platform via Concert smart APIs.

The agent we build will be responsible for:

- Receiving a high-level task from our Supervisor.
- Translating that task into a specific API call that Concert's native AI understands.
- Receiving the AI-generated insights and prioritized actions directly from Concert.
- Passing this intelligent response back to our Supervisor, which can then combine it with insights from other tools to form a complete plan.

---

#### Defining your first agent ⌨️

With your ADK connected to your watsonx Orchestrate SaaS instance, you’re ready to test your setup by building your first agent! 🥳

> [Click to learn more](https://developer.watson-orchestrate.ibm.com/)

In watsonx Orchestrate, agents are defined with `YAML` or `JSON` files. The agent specification file describes the agent’s core details, such as its _name, kind, instructions_ for the LLM, and the _tools_ it can use.

When you build agents with the ADK, you write this specification yourself, giving you full control over what your agent can do and how it behaves. More advanced agents can include _custom tools, collaborators, or integrations_

---

1. Navigate to the agent's YAML file:

   Location: `~/Distributed_Platforms/agents/concert.yaml`

   Open the file in a **plain text editor** (e.g., VSCode, Sublime Text, or a command-line editor like nano or vi). Then, copy and paste the following code and save it.

```YAML
spec_version: v1
kind: native
name: concert_agent
description: >
    This agents helps answer question using knowledge base. Your task is to extract relevant cves , description , wx_recommendation , severity  from knowledge base.
instructions: >
    if user asks question use concert_db knowledge_base to answer it.
    Return  details using knowledge base.  Your task is to extract relevant cves , description , wx_recommendation , severity  from knowledge base.
    if user asks to fetch alerts or concert alerts use fetch_alerts tool only.
    if user ask to scan image run scan_image tool
llm: watsonx/meta-llama/llama-3-405b-instruct

style: default
knowledge_base:
  - concert_db
tools:
  - scan_image
  - fetch_alerts
```

Your YAML file contains the following properties:

- Agent **name** as _concert_agent_

```YAML
name: concert_agent
```

- This agent is going to use an **LLM** of _llama-3-405b-instruct_

```YAML
llm: watsonx/meta-llama/llama-3-405b-instruct
```

- **Agent's Description** - This description is a critical component that serves two primary audiences: it helps users find your agent and understand its purpose and capabilities, and it allows your agent to describe its function to other agents - this is how they discover it and determine if they can collaborate with it to complete a task.

```YAML
description: >
    This agents helps answer question using knowledge base. Your task is to extract relevant cves , description , wx_recommendation , severity  from knowledge base.
```

- Next, we have **instructions** for the agent. These instructions should be provided in natural language and need to include essential details, such as the specific tools available and clear guidance on how and when to use them

```YAML
instructions: >
    if user asks question use concert_db knowledge_base to answer it.
    Return  details using knowledge base.  Your task is to extract relevant cves ,  description , wx_recommendation , severity  from knowledge base.
    if user asks to fetch alerts or concert alerts use fetch_alerts tool only.
    if user ask to scan image run scan_image tool
```

> For this lab, we are using offline API responses stored in Elasticsearch instead of making live API calls. This approach ensures a fast and consistent lab experience by avoiding network delays. In a real-world production environment, your agent's tools would be configured to call the product's live APIs directly.\_

- **knowledge_base** - This property connects your agent to a knowledge base, providing it with relevant information.

```YAML
knowledge_base:
  - concert_db
```

- Finally, we have the agent's **tools**. Tools are the core functionalities that enable the agent to perform its tasks

```YAML
tools:
  - scan_image
  - fetch_alerts
```

> NOTE: In your YAML file, you can define a collaborators property. This is used to list other agents that your agent needs to talk to. For this lab, our agent does not have any collaborators, so we will not be defining this property. For example, in the supervisor agent you'll interact with, we defined two collaborators:\_

```YAML
collaborators:
  - packer_agent
  - terraform_agent
```

> NOTE: You will add `concert_agent` and `Jenkins_agent` as collaborators through the UI at a later step

---

#### Agent Knowledge Base 📁

> You can define knowledge bases using `YAML` or `JSON`, and import them to your active environment using the ADK CLI.

2. Navigate to the agent's knowledge base:

   Location: `~/ agentic-ai-for-itops/Distributed_Platforms/knowledge_base/concertdb.yaml.template`

3. Open the file in a **plain text editor** (e.g., VSCode, Sublime Text, or a command-line editor like nano or vi). Then, copy and paste the following code and save it.

```YAML
spec_version: v1
kind: knowledge_base
name: concert_db
description: >
   This knowledge base is having Concert logs. Use this knowledge to answer user queries.
prioritize_built_in_index: false
conversational_search_tool:
   index_config:
      - elastic_search:
         url: ${ELASTICSEARCH_HOST}
         index: concertindex
         port: "${ELASTICSEARCH_PORT}"
         field_mapping:
            title: title
            body: body
```

> Note: Elasticsearch credentials will be shared by the instructor. You will update your  `.env ` file with ES username and password

Execute the import script again to populate the ElasticSearch values:

```
./import-all.sh
```

---

#### Agent Tool Configuration 🛠️

> Within the ADK, a tool is simply any Python function that you wanted to write and you annotate it with a tool annotation.

4. Navigate to the agent's tools folder:
   Location: `~/ agentic-ai-for-itops/Distributed_Platforms/tools`

We have two tools that our agent uses:

- `fetch_alerts` – _Fetches and processes Concert-related alerts._
- `scan_image` – _Scans container images for vulnerabilities or security issues._

5. Navigate to the agent's **scan image tool**:
   Location: `~/ agentic-ai-for-itops/Distributed Platforms/tools/scan_image.py`
6. Open the file in a **plain text editor** (e.g., VSCode, Sublime Text, or a command-line editor like nano or vi). Then, copy and paste the following code and save it.

```Python

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from datetime import datetime
import traceback
import logging
import os
import sys
import importlib.util

# ----------------------------------------------------------
# 🔍 Find latest tool directory
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
# 🧪 Scan latest Podman image tool (no input needed)
# ----------------------------------------------------------
@tool(permission=ToolPermission.READ_WRITE)
def scan_image():
    """
    Automatically fetches the latest built Podman image tag from the remote VM
    and scans it. No input needed — it discovers newest image locally.
    """
    try:
        # Import SSH executor dynamically
        ssh_module = import_latest_module("ssh_executor.py", "ssh_executor")
        RemoteExecutorTool = ssh_module.RemoteExecutorTool
        executor = RemoteExecutorTool()

        logger = logging.getLogger("scan_latest_image")
        logging.basicConfig(level=logging.INFO)

        logger.info("🔎 Detecting latest built Podman image on remote server...")

        # ✅ Get latest local Podman image by creation time
        # Filters out <none> tags and picks the most recent valid tag
        get_latest_image_cmd = r"""
        podman images --sort=created --format "{{.Repository}}:{{.Tag}}" \
        | grep -v "<none>" \
        | head -1
        """

        res = executor.run_command(get_latest_image_cmd)
        image = res.get("stdout", "").strip()

        if not image:
            raise Exception("❌ Failed to detect latest Podman image on remote host")

        logger.info(f"📦 Latest local image detected: {image}")

        # ✅ Optional: ensure image exists locally (no pull)
        # (remove this if you want to pull always)
        logger.info(f"🧪 Scanning {image} on remote VM...")
        scan_cmd = f"podman scan {image} || echo 'fallback scan - simulated clean'"

        result = executor.run_command(scan_cmd)

        scan_output = result.get("stdout", "") if isinstance(result, dict) else str(result)

        vulnerabilities = [
            line for line in scan_output.splitlines()
            if "CVE-" in line
        ]

        scan_result = {
            "image_full": image,
            "affected_service": "qotd-rating-service",
            "vulnerabilities": vulnerabilities,
            "scanned_at": datetime.utcnow().isoformat(),
            "stdout": scan_output
        }

        logger.info(f"✅ Scan complete — {len(vulnerabilities)} vulnerabilities found")

        return {"status": "success", "scan_result": scan_result}

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    


```

> NOTE: If a tool (part of your agent) needs to interact with an external application or service, you must define a connection in your YAML specification file.
> A connection represents this dependency and contains all the necessary information (like API keys or endpoints) for agents, tools, or knowledge bases to securely authenticate and interact with that external system.

After defining the connection, you can associate it with your agent's tools. See this example - NOT applicable for this lab.

```
@tool(
    expected_credentials=[
        {"app_id": MY_APP_ID, "type": ConnectionType.API_KEY_AUTH}
```

> For more detail on connections see this [link](https://developer.watson-orchestrate.ibm.com/connections/overview)

7. Navigate to the agent's **fetch alerts** tool:
   location: `~/ agentic-ai-for-itops/Distributed_Platforms/tools/fetch_alerts.py`
8. Open the file in a **plain text editor** (e.g., VSCode, Sublime Text, or a command-line editor like nano or vi). Then, copy and paste the following code and save it.

```python

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from langchain_ibm import ChatWatsonx
import traceback
import json
from jinja2 import Template
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from pydantic import BaseModel, Field

from ssh_executor import RemoteExecutorTool
from dotenv import load_dotenv
import os
load_dotenv()
from build_image import build_image


def extract_json_array( content: str) -> list:
    """Extract JSON array from LLM response"""
    try:
        # Find JSON array in response
        start = content.find('[')
        end = content.rfind(']') + 1
        if start >= 0 and end > start:
            json_str = content[start:end]
            return json.loads(json_str)
    except Exception as e:
        print("Failed to extract JSON array, using defaults", error=str(e))

    # Fallback to default commands
    return [
        "apk update",
        "apk upgrade --no-cache",
        "apk add --no-cache curl wget ca-certificates"
            ]

@tool(permission=ToolPermission.READ_WRITE)
def fetch_alerts():
    '''
    return alerts in list

    '''
    return   [{
                "alert_id": "ALERT-2025-001",
                "cve_id": "CVE-2022-2068",
                "severity": "high",
                "affected_service": "qotd-rating-service",
                "affected_image": "registry.gitlab.com/quote-of-the-day/qotd-ratings-service:v5.1.0",
                "description": "OpenSSL vulnerability affecting Alpine Linux base image. The c_rehash script does not properly sanitise shell metacharacters to prevent command injection.",
                "remediation": "Update OpenSSL package to latest version and rebuild container image",
                "detected_at": datetime.now().isoformat(),
                "source": "Concert Security Scanner"
            },
        ]
```

---

### Deploy your agent to your watsonx Orchestrate instance

Navigate to: `/agentic-ai-for-itopsops/Distributed_Platforms`

9. First, we need to Import the Tools. In your ADK terminal input the following:

```
orchestrate tools import -k python -f ./tools/scan_image.py -r ./tools/requirements.txt -p ./tools
```

```
orchestrate tools import -k python -f ./tools/fetch_alerts.py -r ./tools/requirements.txt -p ./tools
```

10. Secondly, we will import knowledge bases

```
orchestrate knowledge-bases import -f ./knowledge_base/concertdb.yaml -a es_creds
```

11. Lastly, we will import Agent yaml

```
orchestrate agents import -f ./agents/concert.yaml
```

---

### Add the Concert agent as a collaborator to the supervisor agent

12. From the Build agents and tools view, click on the `Supervisor_agent`

<p align="center">
  <img src="images/click_supervisor.png" width=800px />
</p>

13. Scroll down in the profile view to `agents` section and click on `add agent`:

<p align="center">
  <img src="images/add_agent.png" width=800px />
</p>

14. Click `Add from local instance`

<p align="center">
  <img src="images/local_instancec.png" width=800px />
</p>

15. Select `concert_agent`

<p align="center">
  <img src="images/select_concert.png" width=800px />
</p>

16. You can confirm from the Supervisor_Agent card that you have 3 agents
    > You will add Jenkins agent as a collaborator in the next section

<p align="center">
  <img src="images/total_agents.png" width=800px />
</p>

17. Navigate back to your Concert Agent

<p align="center">
  <img src="images/manage_agents.png" width=800px />
</p>

<p align="center">
  <img src="images/concert_navigate.png" width=800px />
</p>

18. Make sure that you deploy!

<p align="center">
  <img src="images/concert_deploy.png" width=800px />
</p>

<p align="center">
  <img src="images/concert_deploy2.png" width=800px />
</p>

---

#### Now we can see it in action in our Orchestrate interface!

Ask queries such as `Fetch Alerts` to see the agent work.

<p align="center">
  <img src="images/concert_agent_test.png" width=800px />
</p>

---

<p align="center">✨ You have now completed your Concert agent with ADK 🎊 Let's now dive into creating a Jenkins Agent with MCP! ✨ </p>

---

## Step 3 – Jenkins Agent

Jenkins is an automation server for CI/CD pipelines. The Jenkins _agent_ is specialized execution agent that provides CI/CD capabilities (building, testing, pushing images, updating git) but does NOT make orchestration decisions. The agent receives specific, atomic commands from the Supervisor like "push this image to this registry" and simply executes them.

Jenkin's main capabilities include:

- Triggering build jobs for applications or images.
- Managing pipeline execution for deployments.
- Integrating with Git repositories and other tools for automated DevOps.

To explore how Orchestrate connects with external automation systems, you’ll integrate a **Jenkins MCP Server**. This step simulates connecting your agents to continuous integration workflows or operational pipelines.

---

### ℹ️ Before we start - What is MCP?!

MCP (Model Context Protocol) is like a USB-C for AI: it provides a universal interface for connecting AI applications to external systems such as:

- Databases (e.g., Postgres, SQL)
- Content repositories (e.g., Google Drive, GitHub)
- Business tools (e.g., Slack, Notion)
- Development environments (e.g., IDEs, CI/CD pipelines)

Instead of building custom integrations for each data source, developers can use MCP to expose their systems via MCP servers, and AI applications (called MCP clients) can connect to these servers to retrieve data or perform actions.

MCP consists of three main components

> **MCP Servers**
>
> - Expose data, tools, or workflows to AI clients.
> - Can be built using SDKs in languages like Python, Java, C#, etc.
> - Examples: GitHub, Slack, Docker, web search engines.

> **MCP Clients**
>
> - AI applications that send structured requests to MCP servers.
> - Handle sessions, parse responses, and manage context.
> - Examples: Claude.ai, IBM BeeAI, Microsoft Copilot Studio.

> **MCP Hosts**
>
> - Environments that manage multiple clients and coordinate interactions.

📍 [Learn more about MCP from Anthropic](https://www.anthropic.com/news/model-context-protocol)

---

**The Jenkins MCP Server Plugin** is the official Jenkins plugin that installs the MCP server functionality directly onto your Jenkins instance. It implements the server-side Model Context Protocol, effectively turning your Jenkins automation server into a native MCP-compliant tool that AI clients can communicate with.

> This plugin automatically exposes core Jenkins functions—such as triggerBuild, getJob, getBuildLog, and getStatus—as standardized "tools" that your AI Supervisor can discover and invoke. It requires no special setup, as it installs the necessary API endpoints automatically and reuses the standard Jenkins authentication (like API tokens) for secure access.

👀 [Check out the Jenking MCP Server Plugin](https://plugins.jenkins.io/mcp-server/)

---

### Steps for Setting Up

### Setup your Github
We will be utilization quote of the day demo app for this lab.
You will have to fork the github repository `https://github.com/ritu-patel/Qotd-App.git` 
If you need help with how to fork the github repository - https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo?tool=webui 

Fork example
<p align="center">
  <img src="images/git_fork.png" width=800px />
</p>

#### Get Jenkins Instance

1. Go to [cloud.ibm.com/resources](cloud.ibm.com/resources)

<p align="center">
  <img src="images/jenkins_open_code_engine.png" width=800px />
</p>

2. Click on `jenkins-app` under application

<p align="center">
  <img src="images/jenkins_click_app.png" width=800px />
</p>

3. Go to the domain mappings and get the public url. ❗ Save this url without https:// for later use.

<p align="center">
  <img src="images/jenkins_domain.png" width=800px />
</p>

4. When you access Jenkins URL from previous step, you will be prompted with username and password. ➡️ **The username is admin and the password will be provided by your lab instructor.**

<p align="center">
  <img src="images/jenkins_url.png" width=800px />
</p>

5. Update credentials in Jenkins

Go to Jenkins url from above then click on settings icon on top right

<p align="center">
  <img src="images/jenkins_settings.png" width=800px />
</p>

6. Go to Credentials

![img](images/jenkins_manage_creds.png)

7. Edit the credentials with your own Git url, Git credentials and Quay credentials

- `git_repo-creds` the username will be `GIT_REPO` and password is `<your Github url>`
- `quay-creds` should hold `<your quay username>` and `<your quay password>`
- `git-creds` should contain `<your git username>` and the  `<your github token>`

Below steps will walk you through updating these three variables.

<p align="center">
  <img src="images/jenkins_manage_creds_list.png" width=800px />
</p>


Once the github repository is forked to your github account. Get that URL. For example: https://github.com/ritu-patel/Qotd-App.git
Again this credential only holds the github URL for your forked repo. For lab purposes, github URL is stored as credentials and it is not a standard practice.

First click on the GIT_REPO
<p align="center">
  <img src="images/jenkins_git_repo_00.png" width=800px />
</p>

Then click on update 
<p align="center">
  <img src="images/jenkins_git_repo_01.png" width=800px />
</p>

For password here, put your github url. For example https://github.com/ritu-patel/Qotd-App.git

<p align="center">
  <img src="images/jenkins_git_repo_02.png" width=800px />
</p>


Similarly update the Quay credentials. Update username and password with your quay credentials. Then click Save

<p align="center">
  <img src="images/jenkins_quay_01.png" width=800px />
</p>

Now lets update git-creds credentials. Update your public github username and token/password for the forked repo above. Then click Save

click on
<p align="center">
  <img src="images/jenkins_git_creds_update.png" width=800px />
</p>

then update
<p align="center">
  <img src="images/jenkins_git_token.png" width=800px />
</p>

#### Connect Jenkins to watsonx Orchestrate

1. Go to Agent Builder in watsonx Orchestrate by clicking on hamburger menu icon on the top left
<p align="center">
  <img src="images/agent_builder.png" width=800px />
</p>

2. Go to Tools.

<p align="center">
  <img src="images/create_tools.png" width=800px />
</p>

3. Click on **"Add from file or MCP server"**.

<p align="center">
  <img src="images/add_mcp_01.png" width=800px />
</p>

4. Import from MCP Server.

<p align="center">
   <img src="images/add_mcp_02.png" width=800px />
 </p>

5. Add MCP Server.

<p align="center">
  <img src="images/add_mcp_03.png" width=800px />
</p>

6. Fill out details for the MCP Server:

Make sure you get the Jenkins Instance URL from above to replace the `<jenkins-url>` below.
❗ By default `<user>` is **admin** and `<password>` will be provided to you by your lab instructor.

- Server name: `jenkins_dev`
- Description: `This is my Jenkins dev server`
- Select Connection: `None`
- Install command: replace `<user>`, `<password>`, `<jenkins-url>` in the command below:

```
uvx mcp-proxy https://<user>:<password>@<jenkins-url>/mcp-server/mcp --transport streamablehttp --header mcp-session-id 6e9d4c68-39b6-4fc5-aa05-31d7c1cb5afe
```

For example,

```
uvx mcp-proxy https://admin:726d8da7968f47dfa917b9be3ffff2f7@jenkins-app.20nqsmcqvh0j.us-south.codeengine.appdomain.cloud/mcp-server/mcp --transport streamablehttp --header mcp-session-id 6e9d4c68-39b6-4fc5-aa05-31d7c1cb5afe
```

### URL Instructions

Connection details screenshot:

<p align="center">
    <img src="images/mcp_conn_details.png" width=800px />
  </p>

Click on 'Connect' and wait for connection successful message then click on **Done.**

<p align="center">
    <img src="images/mcp_conn_success.png" width=800px />
  </p>

7. Finally, **activate tools** by toggling them on within this MCP server. Then close the window by click on x top right.

   ![Activate tools](images/toggle_on.png)

8. Once tools are activated close this window. Go to All Agents and Create Agent

> As a reminder - An agent is an AI-powered entity that can autonomously reason, plan, and act—often using tools to complete tasks. Agents use context and goals to decide what actions to take.

![Create agent](images/jenkins_create_agent.png)

10. Add following name description

    Name = `jenkins_agent`
    Description = `This agent runs Jenkins jobs`

    ![Description](images/jenkins_agent_name.png)

11. Go to the Toolset section and click on Add tool

> As a reminder - A tool is a system or service (like Jenkins, GitHub, Slack) that performs a specific function—e.g., running builds, storing code, or sending messages. Tools are typically accessed via APIs.\_

![Add tool](images/jenkins_create_tools.png)

12. Click on Add from file or MCP server

    ![Add MCP](images/jenkins_add_mcp.png)

13. Import from MCP server

    ![import mcp](images/jenkins_import_mcp.png)

14. Select your jenkins server from "Select MCP server"

    ![select mcp](images/jenkins_select_mcp.png)

15. Turn the toggle on for all the tools

    ![toggle](images/jenkins_togggle.png)

16. Add the following behavior in the behavior section which are the set of instructions or prompt for your agent

```Text
The Jenkins IT Agent is a specialized DevOps assistant designed to interact with Jenkins CI/CD systems. It can interpret natural language commands to manage build pipelines, trigger jobs, check statuses, retrieve logs, and handle other operational workflows.
The agent intelligently extracts Jenkins job names and parameters from user requests and executes the correct API or tool actions (e.g., triggerBuild, getBuildStatus, getLastBuildLog, etc.).

Core Responsibilities:
Understand user intents like “trigger the build for frontend pipeline”, “check status of deploy-job”, etc.
Extract Jenkins job names, build numbers, and parameters from text.
Trigger, monitor, and report on Jenkins builds.
Retrieve build logs or artifacts as needed.
Maintain safe operational boundaries (read-only actions where necessary, confirmation before production changes).
```

![behavior](images/jenkins_behavior.png)

18. Ask sample questions such as `show the health status of my jenkins` or `list all my jenkins jobs`

![questions](images/jenkins_sample_questions.png)

Expand the show reasoning to see how orchestrate is calling MCP tool from natural language

![showReasoning](images/jenkins_show_reasoning.png)

![showReasoning](images/jenkins_show_reasoning2.png)

As you can see the Supervisor is calling the `getStatus` tool through the Jenkins agent and you can see the output given back to the Supervisor.

19. Lets add this jenkins agent to Supervisor Agent

Go to Manage Agents

<p align="center">
    <img src="images/jenkins_manage_agents.png" width=800px />
  </p>

Click on Supervisor Agent

<p align="center">
    <img src="images/jenkins_supervisor_01.png" width=800px />
  </p>

Scroll down to find "Add agent"

<p align="center">
    <img src="images/jenkins_supervisor_02.png" width=800px />
  </p>

Click on "Add from local"

  <p align="center">
    <img src="images/jenkins_supervisor_03.png" width=800px />
  </p>

Select your jenkins_agent

  <p align="center">
    <img src="images/jenkins_supervisor_04.png" width=800px />
  </p>
  You should see the success message
  <p align="center">
    <img src="images/jenkins_supervisor_05.png" width=800px />
  </p>

---

20. Lets Deploy the jenkins agent

Go back to manage agents and open your jenkins_agent

<p align="center">
    <img src="images/jenkins_manage_agents.png" width=800px />
  </p>

<p align="center">
  <img src="images/jenkins_deploy_01.png" width=800px />
</p>

<p align="center">
  <img src="images/jenkins_deploy_02.png" width=800px />
</p>

Once you receive success message, navigate back to "Manage agents"

<p align="center">
  <img src="images/jenkins_deploy_03.png" width=800px />
</p>

---

Let's take a look at the YAML for the Jenkins Agent

```YAML
spec_version: v1
kind: native
name: jenkins_agent
description: >
  This agent runs Jenkins jobs
instructions: >
  The Jenkins IT Agent is a specialized DevOps assistant designed to interact with Jenkins CI/CD systems. It can interpret natural language commands to manage build pipelines, trigger jobs, check statuses, retrieve logs, and handle other operational workflows. The agent intelligently extracts Jenkins job names and parameters from user requests and executes the correct API or tool actions (e.g., triggerBuild, getBuildStatus, getLastBuildLog, etc.).

  Core Responsibilities:
  Understand user intents like "trigger the build for frontend pipeline", "check status of deploy-job", etc.
  Extract Jenkins job names, build numbers, and parameters from text.
  Trigger, monitor, and report on Jenkins builds.
  Retrieve build logs or artifacts as needed.
  Maintain safe operational boundaries (read-only actions where necessary, confirmation before production changes).

llm: watsonx/meta-llama/llama-3-405b-instruct

style: default

tools:
  - jenkins_dev:getJob
  - jenkins_dev:getBuildLog
  - jenkins_dev:triggerBuild
  - jenkins_dev:getJobs
  - jenkins_dev:getStatus
  - jenkins_dev:getBuild
  - jenkins_dev:getJobScm
  - jenkins_dev:getBuildScm
```

**Here’s what this code means:**

The **name** and **description** fields (lines 3–5) identify this configuration as the Jenkins agent and describe its capabilities. As mentioned the Jenkins agent is specialized execution agent that provides CI/CD capabilities (building, testing, pushing images, updating git) but does NOT make orchestration decisions.

```YAML
name: jenkins_agent
description: >
  This agent runs Jenkins jobs
```

The **instructions** section (lines 6–17) acts like the logic guide for the LLM. It explains what the agent is responsible for and core responsibilities.

```YAML
instructions: >
  The Jenkins IT Agent is a specialized DevOps assistant designed to interact with Jenkins CI/CD systems. It can interpret natural language commands to manage build pipelines, trigger jobs, check statuses, retrieve logs, and handle other operational workflows. The agent intelligently extracts Jenkins job names and parameters from user requests and executes the correct API or tool actions (e.g., triggerBuild, getBuildStatus, getLastBuildLog, etc.).

  Core Responsibilities:
  Understand user intents like "trigger the build for frontend pipeline", "check status of deploy-job", etc.
  Extract Jenkins job names, build numbers, and parameters from text.
  Trigger, monitor, and report on Jenkins builds.
  Retrieve build logs or artifacts as needed.
  Maintain safe operational boundaries (read-only actions where necessary, confirmation before production changes).
```

The llm field (line 18) specifies the reasoning model (watsonx/meta-llama/llama-3-405b-instruct) that interprets user queries and applies these instructions.

Finally, the **tools** section (line 22) lists the tool available to the agent, we can see a set of 8 jenkins_dev tools that will perform a variety of functions form triggering builds to getting the status. You can check out the tool code in the tools folder.

```YAML
tools:
  - jenkins_dev:getJob
  - jenkins_dev:getBuildLog
  - jenkins_dev:triggerBuild
  - jenkins_dev:getJobs
  - jenkins_dev:getStatus
  - jenkins_dev:getBuild
  - jenkins_dev:getJobScm
  - jenkins_dev:getBuildScm
```

---

<p align="center"> Let's take a moment to review the agents that we imported in Step 1 👀 </p>

---

## Step 4 – Packer Agent

> ❗ This agent & the corresponding tools have already been imported in step 1. Below is to build understanding and ensure your agent and tools are ready to go.

---

[Packer](https://developer.hashicorp.com/packer) is an open-source tool that automates the creation of machine images for multiple platforms from a single configuration file. It’s designed to be fast, consistent, and repeatable. Core capabilities include:

- Multi-platform image builds – Create identical images for cloud providers, containers, and virtualization platforms.
- Provisioning support – Integrate with tools like Ansible, Chef, or shell scripts to configure images during build.
- Automation & consistency – Enables automated, version-controlled image creation for reliable deployments.

---

The Packer Agent automates container image creation using Packer templates. It builds patched images based on pipeline updates and coordinates post-build validation.
It integrates with Jenkins pipelines to rebuild patched or updated images whenever new dependencies or fixes are available.

---

### Check out the Packer agent:

Take a moment to review the YAML file we have created:

```YAML
spec_version: v1
kind: native
name: packer_agent
description: >
        The Packer Agent automates container image creation using pre-defined templates.
        It builds the patched image based on updated dependencies or fixes received from the Jenkins pipeline.
instructions: >
        Use Packer CLI or API to build a container image using the provided Packer template.
        Employ Docker or Podman as the backend builder.
        Once the image build is complete, notify the Security Agent for post-build scanning and validation.
        use build_image tool only when asked for building new image.
        use update_deployment_yaml tool when you asked to update the deployment yaml file
llm: watsonx/meta-llama/llama-3-405b-instruct
style: default
tools:
- update_deployment_yaml
- build_image
```

#### Here's what the code means:

The **name** and **description** fields identify this configuration as the Packer Agent.

```YAML
name: packer_agent
description: >
        The Packer Agent automates container image creation using pre-defined templates.
        It builds the patched image based on updated dependencies or fixes received from the Jenkins pipeline.
```

The **instructions** section outlines the agent’s responsibilities and logic. It uses the Packer CLI or API to build images with Docker or Podman. After building, it should notify the Security Agent for scanning. It also specifies when to use each tool:

- Use `build_image` only when asked to build a new image.
- Use `update_deployment_yaml` only when asked to update the deployment manifest.

```YAML
instructions: >
        Use Packer CLI or API to build a container image using the provided Packer template.
        Employ Docker or Podman as the backend builder.
        Once the image build is complete, notify the Security Agent for post-build scanning and validation.
        use build_image tool only when asked for building new image.
        use update_deployment_yaml tool when you asked to update the deployment yaml file
```

The **llm** field specifies the reasoning model: watsonx/meta-llama/llama-3-405b-instruct. This model interprets user queries and applies the instructions.

Finally, the **tools** section lists the tools available to this agent:

- `update_deployment_yaml` for modifying deployment manifests.
- `build_image` for creating container images.

```YAML
tools:
- update_deployment_yaml
- build_image
```

Check out the tool files for Packer here:
location: `~/ agentic-ai-for-itops/Distributed_Platforms/tools/build_image.py`
location: `~/ agentic-ai-for-itops/Distributed_Platforms/tools/update_deployment_yaml.py`

---

Make sure that you have Packer deployed before moving on!

Click on the Packer Agent
![image](https://github.ibm.com/ibm-us-fsm-ce/agentic-ai-for-itops/assets/448799/7e567d91-5484-479a-bb59-c00913017901)

Then click deploy!
![image](https://github.ibm.com/ibm-us-fsm-ce/agentic-ai-for-itops/assets/448799/5c6493a1-9581-4bfc-b94a-b18d4f011e43)

---

<p align="center"> Onto the last specialized agent - Terraform! ✨ </p>

---

## Step 5 – Terraform Agent

> ❗ This agent & the corresponding tools have already been imported in step 1. Below is to build understanding and ensure your agent and tools are ready to go.

---

The Terraform Agent automates infrastructure and manifest deployment on OpenShift using [Terraform](https://developer.hashicorp.com/terraform). It reads updated manifests from Git, applies them to redeploy patched images, and coordinates with the Supervisor Agent once updates are complete. The Terraform agent in this context is designed to:

- Apply and manage infrastructure configurations using predefined templates.
- Provision, modify, or tear down resources across hybrid environments in a consistent and repeatable way.
- Enable automated workflows for infrastructure deployment as part of DevOps and IT operations processes.

---

### Check out the Terraform Agent:

Take a moment to review the YAML file we have created:

```YAML
spec_version: v1
kind: native
name: terraform_agent
description: >
        The Terraform Agent automates infrastructure and manifest deployment on OpenShift.
        It reads the updated manifests from Git and applies them to redeploy the patched image.
instructions: >
        After the GIT Agent pushes new manifests, use Terraform to apply changes to the OpenShift environment.
        Run `terraform plan` to preview updates and `terraform apply` to enforce them.
        Notify the Orchestrator Agent once the apply operation completes successfully.
llm: watsonx/meta-llama/llama-3-405b-instruct
style: default
tools:
- deploy_image
```

#### What does the code mean:

The **name** and **description** fields identify this configuration as the Terraform Agent. Its role is to automate infrastructure and manifest deployment on OpenShift. It reads updated manifests from Git and redeploys patched images.

```YAML
name: terraform_agent
description: >
        The Terraform Agent automates infrastructure and manifest deployment on OpenShift.
        It reads the updated manifests from Git and applies them to redeploy the patched image.
```

The **instructions** section outlines the agent’s responsibilities:

```YAML
        After the GIT Agent pushes new manifests, use Terraform to apply changes to the OpenShift environment.
        Run `terraform plan` to preview updates and `terraform apply` to enforce them.
        Notify the Orchestrator Agent once the apply operation completes successfully.
```

The **llm** field specifies the reasoning model: watsonx/meta-llama/llama-3-405b-instruct, which interprets user queries and applies the instructions.

The **style** field is set to default, meaning the agent follows standard interaction behavior.

Finally, the **tools** section lists the available tool:

- `deploy_image` – used to apply the updated image to the OpenShift environment.

```YAML
tools:
- deploy_image
```

You can find the Packer tool here:
location: `~/ agentic-ai-for-itops/Distributed_Platforms/tools/deploy_image.py`

---

Make sure that you have the Terraform Agent deployed before moving on!

![image](https://github.ibm.com/ibm-us-fsm-ce/agentic-ai-for-itops/assets/448799/5c6493a1-9581-4bfc-b94a-b18d4f011e43)

---

<p align="center"> 🌟 Finally - the Supervisor Agent! The star of the show! 🌟 </p>

---

## Step 6 – Supervisor Agent

> ❗ This agent & the corresponding tools have already been imported in step 1. Below is to build understanding and ensure your agent and tools are ready to go.

---

Our Supervisor agent is the agent that oversees and coordinates the execution of other agents.

Now that we have checked out and set up all the agents we can check out the YAML file for the supervisor agent to understand how it stiches everything together:

```YAML
spec_version: v1
style: react
name: Supervisor_Agent
llm: watsonx/meta-llama/llama-3-2-90b-vision-instruct
description: >
  You are a Supervisor Agent responsible for understanding user queries and routing them to the most suitable sub-agent.
  You have four agents under your supervision:

  **concert_agent**

  Role: Analyzes security vulnerabilities and risk alerts using the Concert platform.
  Extracts `cve`, `description`, `wx_recommendation`, and `severity` from the Concert knowledge base.
  When asked to fetch or scan alerts, it uses `fetch_alerts` or `scan_image` tools respectively.

  Input: Queries related to vulnerabilities, CVEs, or concert alerts.
  Output: Relevant CVE details or alert summaries.

  **jenkins_agent**

  Role: Manages Jenkins CI/CD pipelines.
  It can interpret commands such as "trigger the build", "get status", or "fetch logs".
  Supports safe operational execution using Jenkins API tools.

  Input: User query about triggering or checking Jenkins jobs.
  Output: Build status, logs, or confirmation of triggered jobs.

  **packer_agent**

  Role: Automates container image creation using Packer templates.
  Builds patched images using Docker or Podman backend.
  If asked to update deployment manifests, it uses the `update_deployment_yaml` tool.

  Input: Query about building or patching images.
  Output: Confirmation and details of built image or YAML update.

  **terraform_agent**

  Role: Automates infrastructure or application deployment on OpenShift using Terraform.
  Reads manifests from Git and applies them to redeploy patched images or infrastructure changes.

  Input: Query about deploying infrastructure or manifests.
  Output: Terraform deployment results and logs.


instructions: >
  Behave as an intelligent router that determines which agent should be triggered based on the user's intent.
  Follow the rules below:

  1. If the query includes:
     - "Concert"
     - "CVE"
     - "security alert"
     - "fetch alerts"
     - "scan image"
     - "recommendation"
     - "wx_recommendation"
     → **Route to `concert_agent`**

  2. If the query includes:
     - "trigger Jenkins job"
     - "run Jenkins"
     - "check build status"
     - "fetch Jenkins logs"
     → **Route to `jenkins_agent`**

  3. If the query includes:
     - "build image"
     - "packer"
     - "patch image"
     - "update deployment yaml"
     → **Route to `packer_agent`**

  4. If the query includes:
     - "deploy"
     - "Terraform"
     - "infrastructure deployment"
     - "apply manifests"
     → **Route to `terraform_agent`**

  5. If the query is unclear:
     - Politely ask the user to clarify what they would like to do or which system (Jenkins, Terraform, etc.) the question is related to.


collaborators:
  - concert_agent
  - jenkins_agent
  - packer_agent
  - terraform_agent
```

#### Let's take a moment to understand how the Supervisor agent works:

The **name** and **description** fields identify this configuration as the Supervisor Agent. Its role is to interpret user input and route it to one of four specialized agents:

- `concert_agent` for security and CVE analysis
- `jenkins_agent` for CI/CD operations
- `packer_agent` for image creation and patching
- `terraform_agent` for infrastructure deployment

```YAML
description: >
  You are a Supervisor Agent responsible for understanding user queries and routing them to the most suitable sub-agent.
  You have four agents under your supervision:

  **concert_agent**

  Role: Analyzes security vulnerabilities and risk alerts using the Concert platform.
  Extracts `cve`, `description`, `wx_recommendation`, and `severity` from the Concert knowledge base.
  When asked to fetch or scan alerts, it uses `fetch_alerts` or `scan_image` tools respectively.

  Input: Queries related to vulnerabilities, CVEs, or concert alerts.
  Output: Relevant CVE details or alert summaries.

  **jenkins_agent**

  Role: Manages Jenkins CI/CD pipelines.
  It can interpret commands such as "trigger the build", "get status", or "fetch logs".
  Supports safe operational execution using Jenkins API tools.

  Input: User query about triggering or checking Jenkins jobs.
  Output: Build status, logs, or confirmation of triggered jobs.

  **packer_agent**

  Role: Automates container image creation using Packer templates.
  Builds patched images using Docker or Podman backend.
  If asked to update deployment manifests, it uses the `update_deployment_yaml` tool.

  Input: Query about building or patching images.
  Output: Confirmation and details of built image or YAML update.

  **terraform_agent**

  Role: Automates infrastructure or application deployment on OpenShift using Terraform.
  Reads manifests from Git and applies them to redeploy patched images or infrastructure changes.

  Input: Query about deploying infrastructure or manifests.
  Output: Terraform deployment results and logs.
```

The **instructions** section acts as the logic guide for the LLM. It defines keyword-based routing rules. For example, if a query includes “CVE” or “scan image,” it should be routed to the concert_agent. If the query is unclear, the agent will ask the user to clarify.

```YAML
instructions: >
  Behave as an intelligent router that determines which agent should be triggered based on the user's intent.
  Follow the rules below:

  1. If the query includes:
     - "Concert"
     - "CVE"
     - "security alert"
     - "fetch alerts"
     - "scan image"
     - "recommendation"
     - "wx_recommendation"
     → **Route to `concert_agent`**

  2. If the query includes:
     - "trigger Jenkins job"
     - "run Jenkins"
     - "check build status"
     - "fetch Jenkins logs"
     → **Route to `jenkins_agent`**

  3. If the query includes:
     - "build image"
     - "packer"
     - "patch image"
     - "update deployment yaml"
     → **Route to `packer_agent`**

  4. If the query includes:
     - "deploy"
     - "Terraform"
     - "infrastructure deployment"
     - "apply manifests"
     → **Route to `terraform_agent`**

  5. If the query is unclear:
     - Politely ask the user to clarify what they would like to do or which system (Jenkins, Terraform, etc.) the question is related to.
```

The **llm** field specifies the reasoning model used to interpret and route queries: watsonx/meta-llama/llama-3-2-90b-vision-instruct.

The **style** field indicates the interaction style of the agent. In this case, it’s set to react, which supports dynamic, responsive interactions.

Finally, the **collaborators** section lists the four sub-agents that the Supervisor Agent can delegate to. These agents are responsible for executing specific tasks based on the routed query.

```YAML
collaborators:
  - concert_agent
  - jenkins_agent
  - packer_agent
  - terraform_agent
```

---

Make sure that you have the Supervisor Agent deployed before moving on!

Click on the Supervisor Agent
![image](https://github.ibm.com/ibm-us-fsm-ce/agentic-ai-for-itops/assets/448799/ea67964e-1445-4d7e-b491-527e9dcd9d31)

Then click deploy!
![image](https://github.ibm.com/ibm-us-fsm-ce/agentic-ai-for-itops/assets/448799/5c6493a1-9581-4bfc-b94a-b18d4f011e43)

---

<p align="center"> 🎊 Congratulations! Now now have our system ready to go through our flow! 🎊 </p>
