cortx-support-bundle-inside-container 📝
Service to generate a support bundle of Cortx logs in a containerised env.
***

## ⚽ Current Functionality
    - sb_interface.py provides an interface for user to request the support-bundle generation.
      it will deploy
        1. PV & PVCs.
        2. Build support_bundle image.
        3. Run the support-bundle pod
      this pod which will be responsible to generate support-bundle and will generate 
      the tarfile at path: "/var/cortx/support_bundle/data/" using PV & PVC

### 💻 Quick Start
    - Pre Requisites:
      - Docker and Kubernetes is installed.
      - kubernetes or docker cluster is up & running
    - Commands 
      - User request to generate support-bundle
        ```bash
        cd cortx-utils
        python3 py-utils/src/support_bundle/sb_interface.py --generate
        # output
        # Support Bundle generated successfully at path:
        '/var/cortx/support_bundle/data/support_bundle.tar.gz' !!!
        ```
