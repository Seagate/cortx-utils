pipeline {
    agent {
        node {
            label 'docker-image-build-centos-7.8'
        }
    }
    
   	environment {
	    GITHUB_CRED = credentials('shailesh-github')
	}


    options {
		timeout(time: 240, unit: 'MINUTES')
		timestamps()
		disableConcurrentBuilds()
        buildDiscarder(logRotator(daysToKeepStr: '30', numToKeepStr: '30'))
		ansiColor('xterm')
	}

    parameters {

        string(name: 'CORTX_RE_BRANCH', defaultValue: 'main', description: 'Branch or GitHash to build docker image', trim: true)
        string(name: 'CORTX_RE_REPO', defaultValue: 'https://github.com/Seagate/cortx-re', description: 'Repository to build docker image', trim: true)

        choice (
            name: 'OS_VERSION', 
            choices: ['centos-7.8.2003'],
            description: 'OS Version'
        )

        choice (
            name: 'ENVIRONMENT', 
            choices: ['internal-ci', 'opensource-ci'],
            description: 'CI Environment'
        )

        choice (
            choices: ['no' , 'yes'],
            description: 'Push newly built Docker image to GitHub ',
            name: 'GITHUB_PUSH'
        )

	}	

    stages {

        stage('Checkout Script') {
            steps {             
                script {
                    checkout([$class: 'GitSCM', branches: [[name: "${CORTX_RE_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${CORTX_RE_REPO}"]]])                
                }
            }
        }

        stage ('Build Docker image') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Build Docker image', script: '''
				echo -e "Running on $HOSTNAME"
                        #Clean Up
                		echo 'y' | docker image prune
                		if [ ! -z \$(docker ps -a -q) ]; then docker rm -f \$(docker ps -a -q); fi
                        if [ $ENVIRONMENT == "internal-ci" ]; then
                	    	docker-compose -f docker/cortx-build/docker-compose.yml build --force-rm  --compress --build-arg GIT_HASH="$(git rev-parse --short HEAD)" cortx-build-internal-$OS_VERSION
		                else
                		    docker-compose -f docker/cortx-build/docker-compose.yml build --force-rm  --compress --build-arg GIT_HASH="$(git rev-parse --short HEAD)" cortx-build-$OS_VERSION
		                fi
                		echo 'y' | docker image prune
		                '''
			   }
			}

        stage ('Validation') {
			steps {
				script { build_stage = env.STAGE_NAME }
				               
                checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: 'main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: '/mnt/docker/tmp/cortx-workspace'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: false, recursiveSubmodules: true, reference: '', shallow: true, trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[url: 'https://github.com/Seagate/cortx']]]

                sh label: 'Validate Docker image', script: '''
                if [ $ENVIRONMENT == "internal-ci" ]; then
                    docker run --rm -v /mnt/docker/tmp/cortx-workspace:/cortx-workspace -v /mnt/docker/tmp/artifacts:/var/artifacts ghcr.io/seagate/cortx-re/cortx-build-internal:$OS_VERSION make clean build
                else    
                    docker run --rm -v /mnt/docker/tmp/cortx-workspace:/cortx-workspace -v /mnt/docker/tmp/artifacts:/var/artifacts ghcr.io/seagate/cortx-build:$OS_VERSION make clean build
                fi
                echo "CORTX Packages generated..."
                grep -w "cortx-motr\\|cortx-s3server\\|cortx-hare\\|cortx-csm_agent\\|cortx-csm_web\\|cortx-sspl\\|cortx-s3server\\|cortx-prvsnr" /mnt/docker/tmp/artifacts/0/cortx_iso/RELEASE.INFO
                cat /mnt/docker/tmp/artifacts/0/cortx_iso/RELEASE.INFO
                rm -rf /mnt/docker/tmp/
                '''
			}
		}

        stage ('Push  Docker image') {
            when {
                expression { params.GITHUB_PUSH == 'yes' }
            }
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Build Docker image', script: '''
                docker login ghcr.io -u ${GITHUB_CRED_USR} -p ${GITHUB_CRED_PSW}
                docker-compose -f docker/internal-ci/docker-compose.yml push cortx-build-internal-$OS_VERSION
                '''
			}
		}
    }

	post {

		always {
			script {

				def recipientProvidersClass = [[$class: 'RequesterRecipientProvider']]
                
                def mailRecipients = "CORTX.DevOps.RE@seagate.com"
                emailext ( 
                    body: '''${SCRIPT, template="release-email.template"}''',
                    mimeType: 'text/html',
                    subject: "[Jenkins Build ${currentBuild.currentResult}] : ${env.JOB_NAME}",
                    attachLog: true,
                    to: "${mailRecipients}",
					recipientProviders: recipientProvidersClass
                )
            }
        }
    }
}