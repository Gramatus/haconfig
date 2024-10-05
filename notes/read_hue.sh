
#!/bin/bash
# ./read_hue.sh -a scenes -t <api_key>

set -euo pipefail
# set x # for debugging

mkdir -p downloaded

BRIDGE_IP=192.168.50.52
MODE="v1"
RESOURCE_ID=""

while getopts t:a:b:r:2 flag
do
    case "${flag}" in
        t) TOKEN=${OPTARG};;
        a) API=${OPTARG};;
        b) BRIDGE_IP=${OPTARG};;
        r) RESOURCE_ID=${OPTARG};;
        2) MODE="v2";;
    esac
done

# Hue uses a self-signed cert. Source of cert trust: https://developers.meethue.com/develop/application-design-guidance/using-https/
BRIDGE_ID=ecb5fafffe239991

if [ $MODE = "v2" ]; then
    curl -X GET "https://${BRIDGE_ID}/clip/v2/resource/${API}/${RESOURCE_ID}" \
    --header "hue-application-key: ${TOKEN}" \
    --cacert huebridge_cacert.pem \
    --resolve "${BRIDGE_ID}:443:${BRIDGE_IP}" \
    | jq -s > "downloaded/${API}${RESOURCE_ID}_v2.json"
    echo "/clip/v2/resource/${API}/${RESOURCE_ID} saved to downloaded/${API}${RESOURCE_ID}_v2.json"
fi

if [ $MODE = "v1" ]; then
    curl -X GET "https://${BRIDGE_ID}/api/${TOKEN}/${API}/${RESOURCE_ID}" \
    --cacert huebridge_cacert.pem \
    --resolve "${BRIDGE_ID}:443:${BRIDGE_IP}" \
    | jq -s > "downloaded/${API}${RESOURCE_ID}.json"
    echo "/api/<TOKEN>/${API}/${RESOURCE_ID} saved to downloaded/${API}${RESOURCE_ID}.json"
fi
