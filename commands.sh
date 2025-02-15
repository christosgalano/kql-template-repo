#!/bin/bash

# az login --service-principal \
# --username 28cb0334-d11c-409e-9ace-5a793f7dfcd5 \
# --password 54t8Q~1sDu768lgtsaH2squ_K3gUWjenFmiXbboY \
# --tenant be7a0842-5dc9-4437-9112-d90729f0cabd


# az monitor log-analytics query-pack list --resource-group cyberworkbench-siem


# az monitor log-analytics query-pack create --name --resource-group

# az config set extension.dynamic_install_allow_preview=true

# kql_content=$(cat network.kql)

# az monitor log-analytics query-pack create --name device --resource-group cyberworkbench-siem

for kql_file in ./queries/device/*.kql; do
    echo "Processing $kql_file"
    kql_content=$(cat "$kql_file")
    results=$(az monitor log-analytics query -w a1abdd65-c544-4706-92ba-353350bd557b \
    --analytics-query "$kql_content" | jq 'length')
    echo "Number of results for $kql_file: $results"
done

# az monitor log-analytics query -w a1abdd65-c544-4706-92ba-353350bd557b --analytics-query "$kql_content" | jq '.tables[0].rows | length'
