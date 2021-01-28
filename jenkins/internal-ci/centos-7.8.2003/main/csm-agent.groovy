pipeline {
	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}
    
    parameters {
        string(name: 'branch', defaultValue: 'main', description: 'Branch Name')
    }
	
	environment {
        version = "2.0.0"      
        env = "dev"
		component = "csm-agent"
        os_version = "centos-7.8.2003"
        pipeline_group = "main"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "${release_dir}/components/github/${pipeline_group}/${os_version}/${env}/${component}"

        // Param hack for initial config
        branch="${branch != null ? branch : 'main'}"
    }

	options {
		timeout(time: 60, unit: 'MINUTES')
		timestamps ()
        ansiColor('xterm')
        disableConcurrentBuilds()
	}

	triggers {
        pollSCM 'H/5 * * * *'
    }

	stages {
        stage('Checkout') {
            steps {
                script { build_stage = env.STAGE_NAME }
                checkout([$class: 'GitSCM', branches: [[name: "${branch}"]], doGenerateSubmoduleConfigurations: false,  extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-manager']]])
                
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: '', script: '''
				sed -i 's/gpgcheck=1/gpgcheck=0/' /etc/yum.conf
                yum-config-manager --disable cortx-C7.7.1908,cortx-uploads
				yum-config-manager --add http://cortx-storage.colo.seagate.com/releases/cortx/github/stable/$os_version/last_successful/
				yum-config-manager --add http://cortx-storage.colo.seagate.com/releases/cortx/components/github/main/$os_version/dev/cortx-utils/last_successful/
				yum clean all && rm -rf /var/cache/yum
				yum install -y cortx-prvsnr
				pip3.6 install  pyinstaller==3.5
                '''
            }
        }	
        
        stage('Build') {
            steps {
                script { build_stage = env.STAGE_NAME }
                // Exclude return code check for csm_setup and csm_test
                sh label: 'Build', returnStatus: true, script: '''
                    BUILD=$(git rev-parse --short HEAD)
                    VERSION=$(cat $WORKSPACE/VERSION)
                    echo "Executing build script"
                    echo "VERSION:$VERSION"
                    echo "Python:$(python --version)"
                    ./cicd/build.sh -v $VERSION -b $BUILD_NUMBER -t -i
                '''	
            }
        }
        
        stage ('Upload') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Copy RPMS', script: '''
                    mkdir -p $build_upload_dir/$BUILD_NUMBER
                    cp ./dist/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
                '''
                sh label: 'Repo Creation', script: '''
                    pushd $build_upload_dir/$BUILD_NUMBER
                    rpm -qi createrepo || yum install -y createrepo
                    createrepo .
                    popd
                '''
             }
        }

        stage ('Tag last_successful') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Tag last_successful', script: '''
                    pushd $build_upload_dir/
                    test -L $build_upload_dir/last_successful && rm -f last_successful
                    ln -s $build_upload_dir/$BUILD_NUMBER last_successful
                    popd
                '''
			}
		}

        stage ("Release") {
            //when { triggeredBy 'SCMTrigger' }
            steps {
                script { build_stage = env.STAGE_NAME }
				script {
                	def releaseBuild = build job: 'Main Release', propagate: true, parameters: [string(name: 'release_component', value: "${component}"), string(name: 'release_build', value: "${BUILD_NUMBER}")]
				 	env.release_build = "${BUILD_NUMBER}"
                    env.release_build_location = "http://cortx-storage.colo.seagate.com/releases/cortx/github/$pipeline_group/$os_version/${component}_${BUILD_NUMBER}"
				}
            }
        } 
	}

	post {
		always {
			script {
            	
				echo 'Cleanup Workspace.'
				deleteDir() /* clean up our workspace */

				env.release_build = (env.release_build != null) ? env.release_build : "" 
				env.release_build_location = (env.release_build_location != null) ? env.release_build_location : ""
				env.component = (env.component).toUpperCase()
				env.build_stage = "${build_stage}"

				def toEmail = ""
				def recipientProvidersClass = [[$class: 'DevelopersRecipientProvider'], [$class: 'RequesterRecipientProvider']]
				if ( manager.build.result.toString() == "FAILURE") {
					toEmail = "CORTX.CSM@seagate.com,shailesh.vaidya@seagate.com"
					recipientProvidersClass = [[$class: 'DevelopersRecipientProvider'],[$class: 'RequesterRecipientProvider']]
				}
				emailext (
					body: '''${SCRIPT, template="component-email.template"}''',
					mimeType: 'text/html',
				    subject: "[Jenkins Build ${currentBuild.currentResult}] : ${env.JOB_NAME}",
					attachLog: true,
					to: toEmail,
					recipientProviders: recipientProvidersClass
				)
			}
		}
    }
}