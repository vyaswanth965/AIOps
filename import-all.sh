#!/usr/bin/env bash
set -x

#git lfs install
ENV_PATH="./tools/.env"

if [ -f "$ENV_PATH" ]; then
    set -a                # Automatically export all variables
    source "$ENV_PATH"    # Load .env file from given path
    set +a
    echo "Loaded environment from $ENV_PATH"
else
    echo "Error: .env file not found at $ENV_PATH"
    exit 1
fi

envsubst < ./knowledge_base/concertdb.yaml.template >  ./knowledge_base/concertdb.yaml

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )



for python_tool in  fetch_alerts.py  build_image.py scan_image.py update_deployment_yaml.py deploy_image.py; do
  orchestrate tools import -k python -f ${SCRIPT_DIR}/tools/${python_tool} -r ${SCRIPT_DIR}/tools/requirements.txt -p ${SCRIPT_DIR}/tools
done


orchestrate connections remove --app-id es_creds
orchestrate connections add -a es_creds

orchestrate connections configure -a es_creds --env draft --kind basic --type team

orchestrate connections set-credentials -a es_creds --env draft -u $ELASTIC_USER -p $ELASTIC_PASSWORD



orchestrate knowledge-bases import -f ${SCRIPT_DIR}/knowledge_base/concertdb.yaml -a es_creds


for agent in  concert.yaml  packer.yaml terraform.yaml supervisor.yaml; do
  orchestrate agents import -f ${SCRIPT_DIR}/agents/${agent}
done

