#!/usr/bin/env groovy
pipeline {

        agent {
                node {
                        label 'docker-cp-centos-7.8.2003-node'
                }
        }

        parameters {
                string(name: 'RELEASE_INFO_URL', defaultValue: '', description: 'RELEASE BUILD')
                string(name: 'GIT_TAG', defaultValue: '', description: 'Tag Name')
		string(name: 'TAG_MESSAGE', defaultValue: '', description: 'Tag Message')
		string(name: 'REL_NAME', defaultValue: '', description: 'Release Name')
		string(name: 'REL_ID', defaultValue: '', description: 'Release Id')
		booleanParam(name: 'DEBUG', defaultValue: false, description: 'Select this if you want to Delete the current Tag')
            }
		
		
        environment {
                COMMIT_HASH_CORTX_CSM_AGENT = get_commit_hash("cortx-csm_agent", "${RELEASE_INFO_URL}")
                COMMIT_HASH_CORTX_CSM_WEB = get_commit_hash("cortx-csm_web", "${RELEASE_INFO_URL}")
                COMMIT_HASH_CORTX_HARE = get_commit_hash("cortx-hare", "${RELEASE_INFO_URL}")
                COMMIT_HASH_CORTX_HA = get_commit_hash("cortx-ha", "${RELEASE_INFO_URL}")
                COMMIT_HASH_CORTX_MOTR = get_commit_hash("cortx-motr", "${RELEASE_INFO_URL}")
                COMMIT_HASH_CORTX_PRVSNR = get_commit_hash("cortx-prvsnr", "${RELEASE_INFO_URL}")
                COMMIT_HASH_CORTX_S3SERVER = get_commit_hash("cortx-s3server", "${RELEASE_INFO_URL}")
                COMMIT_HASH_CORTX_SSPL = get_commit_hash("cortx-sspl", "${RELEASE_INFO_URL}")
		COMMIT_HASH_CORTX_UTILS = get_commit_hash("cortx-py-utils", "${RELEASE_INFO_URL}")
		COMMIT_HASH_CORTX_RE = get_commit_hash("cortx-prereq", "${RELEASE_INFO_URL}")
            }

        stages {

        stage ("Display") {
            steps {
                script { build_stage=env.STAGE_NAME }
                echo "COMMIT_HASH_CORTX_CSM_AGENT = $COMMIT_HASH_CORTX_CSM_AGENT"
                echo "COMMIT_HASH_CORTX_CSM_WEB = $COMMIT_HASH_CORTX_CSM_WEB"
                echo "COMMIT_HASH_CORTX_HARE = $COMMIT_HASH_CORTX_HARE"
                echo "COMMIT_HASH_CORTX_HA = $COMMIT_HASH_CORTX_HA"
                echo "COMMIT_HASH_CORTX_MOTR = $COMMIT_HASH_CORTX_MOTR"
                echo "COMMIT_HASH_CORTX_PRVSNR = $COMMIT_HASH_CORTX_PRVSNR"
                echo "COMMIT_HASH_CORTX_S3SERVER = $COMMIT_HASH_CORTX_S3SERVER"
                echo "COMMIT_HASH_CORTX_SSPL = $COMMIT_HASH_CORTX_SSPL"
		echo "COMMIT_HASH_CORTX_UTILS = $COMMIT_HASH_CORTX_UTILS"
		echo "COMMIT_HASH_CORTX_RE = $COMMIT_HASH_CORTX_RE"
		}
        }
		
	stage('Checkout Script') {
            steps {             
                script {
                    checkout([$class: 'GitSCM', branches: [[name: '*/main']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])                
                }
            }
        }
	stage("Tagging") {
	    steps {
		script { build_stage=env.STAGE_NAME }
			script { 
				withCredentials([usernamePassword(credentialsId: 'cortx-admin-github', passwordVariable: 'PASSWD', usernameVariable: 'USER_NAME')]) {
				sh """ bash scripts/release_support/git-tag.sh """    
					}
				}			
			}
		}
	}
}

def get_commit_hash(String component, String release_info) {

    return sh(script: """
            set +x
            if [ "$component" == "cortx-hare" ] || [ "$component" == "cortx-sspl" ] || [ "$component" == "cortx-ha" ] || [ "$component" == "cortx-py-utils" ] || [ "$component" == "cortx-prereq" ]; then
                
                echo \$(curl -s $release_info | grep -w '*.rpm\\|$component\\|uniq' | awk '!/debuginfo*/' | awk -F['_'] '{print \$2}' | cut -d. -f1 |  sed 's/git//g' | grep -v ^[[:space:]]*\$);
					
            elif [ "$component" == "cortx-csm_agent" ] || [ "$component" == "cortx-csm_web" ]; then
                
		echo \$(curl -s $release_info | grep -w '*.rpm\\|$component\\|uniq' | awk '!/debuginfo*/' | awk -F['_'] '{print \$3}' | cut -d. -f1 |  sed 's/git//g' | grep -v ^[[:space:]]*\$);	
            
	    else
		echo \$(curl -s $release_info | grep -w '*.rpm\\|$component\\|uniq' | awk '!/debuginfo*/' | awk -F['_'] '{print \$2}' | cut -d. -f1 |  sed 's/git//g' | grep -v ^[[:space:]]*\$);	
            fi
			
	""", returnStdout: true).trim()
}

