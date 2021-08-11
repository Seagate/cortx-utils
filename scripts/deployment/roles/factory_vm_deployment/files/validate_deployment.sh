#!/bin/bash

pcsStatusFile="/root/cortx_deployment/log/pcs_status.log"
service_filter=(
    "systemd:hare-hax"
    "systemd:s3authserver"
    "systemd:haproxy"
    "systemd:s3backgroundconsumer"
    "systemd:motr-free-space-monitor"
    "systemd:s3backgroundproducer"
    "systemd:sspl-ll"
    "systemd:kibana"
    "systemd:csm_agent"
    "systemd:csm_web"
    "systemd:event_analyzer"
    "service_instances_counter"
    "systemd:cortx_message_bus"
)

count_service_filter=(
    "motr-confd-count"
    "motr-ios-count"
    "s3server-count"
)

for service in ${service_filter[@]}; do
    service_state=$(grep "${service}" "${pcsStatusFile}" | awk '{print $3}')
    for state in ${service_state}; do
      if [ "${state}" != "Started" ]; then
          echo "Failed Service : ${service}"
      fi
    done
done

for service in ${count_service_filter[@]}; do
    service_count=$(grep "${service}" "${pcsStatusFile}" | awk '{print $4}')
    for count in ${service_count}; do
      if [ "${count}" -eq 0 ]; then
          echo "Failed Service : ${service}"
      fi
    done
done