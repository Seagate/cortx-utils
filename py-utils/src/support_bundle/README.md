cortx-support-bundle-inside-container 📝
Service to generate a support bundle of Cortx logs in a containerised env.
***

## ⚽ Current Functionality
    - sb_interface.py provides an interface for user to request the support-bundle generation.
      it will deploy a pod which will be responsible to generate support-bundle and will write 
      the tarfile at path: "/var/cortx/support_bundle/data/" using PV & PVC

### 💻 Quick Start
    - Pre Requisites:
      - Docker and Kubernetes is installed.
      - kubernetes or docker cluster is up & running
    - Commands 
      - Create Persistent Volume and Persistent Volume Claim
        ```bash
        cd cortx-utils
        py-utils/test/support_bundle/deploy_pvc.sh
        # verify
        kubectl get pv
        kubectl get pvc
        ```
      - User request to generate support-bundle
        ```bash
        python3 py-utils/src/support_bundle/sb_interface.py --generate
        # output
        # Support Bundle generated successfully at path:
        '/var/cortx/support_bundle/data/support_bundle.tar.gz' !!!
        ```

