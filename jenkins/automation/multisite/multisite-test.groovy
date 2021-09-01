pipeline {
    agent {
        node {
           label "docker-centos-7.9.2009-node"
        }
    }
    
    options {
		timeout(time: 240, unit: 'MINUTES')
		timestamps()
		disableConcurrentBuilds()
        buildDiscarder(logRotator(daysToKeepStr: '30', numToKeepStr: '30'))
		ansiColor('xterm')
	}

    parameters {

        string(name: 'MULTISITE_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for cortx-multisite', trim: true)
        string(name: 'MULTISITE_REPO', defaultValue: 'https://github.com/Seagate/cortx-multisite/', description: 'Repository URL for multisite', trim: true)
	}	

    stages {

        stage('Checkout Script') {
            steps {             
                script {
                    checkout([$class: 'GitSCM', branches: [[name: "${MULTISITE_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${MULTISITE_REPO}"]]])                
                }
            }
        }
        
        stage ('Execute Test') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Execute Test', script: '''
                #Add s3.seagate.com entry
                echo "$(awk 'END{print $1}' /etc/hosts)      s3.seagate.com" >> /etc/hosts
                pushd ./s3/replication
                    sh ./build_and_test.sh
                popd
                '''
			}
		}	
    }

	post {

		always {
			script {
                env.branch_name = "${MULTISITE_BRANCH}"
                env.repo_url = "${MULTISITE_REPO}"
                env.build_stage = "${build_stage}"
				def recipientProvidersClass = [[$class: 'RequesterRecipientProvider']]
                def mailRecipients = "shailesh.vaidya@seagate.com,kaustubh.deorukhkar@seagate.com,mehmet.balman@seagate.com"

                emailext body: '''${SCRIPT, template="mini_prov-email.template"}''',
                mimeType: 'text/html',
                recipientProviders: [requestor()], 
                subject: "[Jenkins] Multisite Test : ${currentBuild.currentResult}, ${JOB_BASE_NAME}#${BUILD_NUMBER}",
                to: "${mailRecipients}"
            }
        }
    }
}