cortx-support-bundle-inside-container 📝
Service to generate a support bundle of Cortx logs in a containerised env.
***

## ⚽ Current Functionality
    - sb_interface.py provides an interface for user to request the support-bundle generation.
      it will deploy
        1. PV & PVCs.
        2. Build support_bundle image.
        3. Run the support-bundle pod
      this pod which will be responsible for generating support bundle
      # For all components,
        It will collect all the cortx logs present under /var/log dir and will bundle them
        and share on hostpath:- 
        '/var/cortx/support_bundle/data/cortx-support_bundle-<bundle_id>.tar.gz'
      # For specific component,
        It will collect the logs present under /var/log/<component> dir if present,
        at path:- 
        '/var/cortx/support_bundle/data/<component>-support_bundle-<bundle_id>.tar.gz'
        If /var/log/<component> is not present, It will print the status
        Failed: Support-bundle not generated.Please check /var/log/<component> dir exists or not.

### 💻 Quick Start
    - Pre Requisites:
      - Docker and Kubernetes is installed.
      - kubernetes or docker cluster is up & running
    - Commands 
      - User request to generate support-bundle
        ```bash
        cd cortx-utils/py-utils/src/support_bundle/
        python3
        >>> from sb_interface import SupportBundle
        # for all components
        >>> bundle_obj =  SupportBundle.generate('test all comps')
        # for single component
        >>> bundle_obj =  SupportBundle.generate('test csm', components=['csm']) 
        >>> status =  SupportBundle.get_status(bundle_id=bundle_obj.bundle_id)
        >>> print(status)

        # output
        #Success: Support Bundle generated successfully at path: 
        '/var/cortx/support_bundle/data/cortx-support_bundle-<bundle_id>.tar.gz' !!!
        ```
