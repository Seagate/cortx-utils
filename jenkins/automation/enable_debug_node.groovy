#!/usr/bin/env groovy
pipeline { 
    agent {
        node {
            // random node to execute the groovy script - no operations are performed on the node
            label "docker-io-centos-7.8.2003-node"
        }
    }
	
    parameters {
        string(name: 'DEPLOYMENT_NODE_LABEL', defaultValue: 'cleanup_req', description: 'Provide the Jenkins Node label for the node you want switch back online and start cleanup. Cleanup wont executed if node is disabled less then MAXIMUM_ALLOWED_TIME_TO_HOLD_NODE hr. Use FORCE option to override this behaviour',  trim: true)
        choice(name: 'MAXIMUM_ALLOWED_TIME_TO_HOLD_NODE', choices: [ 12, 6, 3, 1 ], description: 'Only enable & cleanup the node that was disabled X hours before. FORCE option will ovverride this behaviour')
        booleanParam(name: 'FORCE', defaultValue: false, description: 'Unlock & Cleanup all the offline Nodes irespective to MAXIMUM_ALLOWED_TIME_TO_HOLD_NODE')
    }	

    triggers {
        cron('H */12 * * *')
    }

    options {
        timeout(time: 5, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm') 
        buildDiscarder(logRotator(numToKeepStr: "30"))
    }

    stages {

        stage ('Enable Offline VMs') {
            steps {
                script {
                    
                    // Enable and cleanup vm based on provided arguments
                    enableOfflineVM("${DEPLOYMENT_NODE_LABEL}")
                }
            }
        }
	}
}	


// Get running node instance
def enableOfflineVM(nodeLabel) {
    
    // Get timestamp of 'ENABLE_VM_OLDER_THEN_X_HRS' hour before  
    offlineTimestamp =   System.currentTimeMillis() - params.MAXIMUM_ALLOWED_TIME_TO_HOLD_NODE.toInteger() * 60 * 60 * 1000
    
    // Iterate all jenkins node
    for (node in Jenkins.instance.nodes) {
        
        node_label = node.getLabelString()

        computer = node.toComputer()
        
        // Filter node with label 'cleanup_req', 'vm_deployment_1n', 'mini_provisioner' and and offline status
        if ( node_label.contains("cleanup_req") && ( node_label.contains("vm_deployment_1n") || node_label.contains("mini_provisioner") )
                && node_label.contains(nodeLabel) ) {

            if (computer.isTemporarilyOffline()) {

				// If 'FORCE' is provided don't consider timestamp comparison
				if ( params.FORCE || computer.getOfflineCause().getTimestamp() < offlineTimestamp ) {
					
					echo "Offline Node  : ${node.getNodeName()} : ${computer.getOfflineCause().toString()} on ${ computer.getOfflineCause().getTime()}" 
                    
                    computer.setTemporarilyOffline(false, computer.getOfflineCause())

					build job: 'Cortx-Automation/Deployment/VM-Cleanup', wait: false, parameters: [string(name: 'NODE_LABEL', value: "${node.getNodeName()}")]            

                }

            } else if ( computer.countBusy()==0 )  {  // This is not part of this job scope, but still it cleanups the online nodes
			
				build job: 'Cortx-Automation/Deployment/VM-Cleanup', wait: false, parameters: [string(name: 'NODE_LABEL', value: "${node.getNodeName()}")]            
			}

        }
    }
}