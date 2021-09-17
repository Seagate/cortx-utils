#!/bin/bash -x

SCRIPT_DIR=$(dirname $0)

deploy_pvc()
{
    # Create Persistent Volume
    kubectl apply -f "$SCRIPT_DIR"/pv.yml
    kubectl apply -f "$SCRIPT_DIR"/pv2.yml

    # Create a Persistent Volume Claim
    kubectl apply -f "$SCRIPT_DIR"/pv-claim.yml
    kubectl apply -f "$SCRIPT_DIR"/pv-claim2.yml

    sleep 5
}

build_image()
{
    # Build the support bundle image
    docker build -f Dockerfile -t support_bundle:1.1 .
}

deploy_pod() {
    # Deploy the support-bundle pod to generate the cortx logs tar.
    kubectl apply -f "$SCRIPT_DIR"/sb-pod.yml
}

delete_pod() {
    kubectl delete pod sb-pod
}

opt=$1
case $opt
in
    --pvc)
        deploy_pvc ;;
    --sb_image)
        build_image ;;
    --sb_pod)
        deploy_pod ;;
    --delete_pod)
        delete_pod ;;
    * ) echo "Invalid option."
    exit ;;
esac