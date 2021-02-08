pipeline {
	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}

    triggers {
        pollSCM 'H/5 * * * *'
    }

	environment {      
        env = "dev"
		component = "cortx-utils"
        branch = "main"
        os_version = "centos-7.8.2003"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "$release_dir/components/github/$branch/$os_version/$env/$component"
    }

	options {
		timeout(time: 60, unit: 'MINUTES')
		timestamps ()
        ansiColor('xterm')
        disableConcurrentBuilds()
	}

	stages {
		stage('Checkout py-utils') {
			steps {
                script { build_stage = env.STAGE_NAME }
                checkout([$class: 'GitSCM', branches: [[name: "*/${branch}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-utils']]])
			}
		}
        
		stage('Build') {
			steps {
                script { build_stage = env.STAGE_NAME }
				sh label: 'Build', script: '''
				yum install python36-devel -y
				pushd py-utils
				python3.6 setup.py bdist_rpm --post-install utils-post-install --post-uninstall utils-post-uninstall --post-uninstall utils-post-uninstall --release="${BUILD_NUMBER}_$(git rev-parse --short HEAD)"
				popd
				
				./statsd-utils/jenkins/build.sh -b $BUILD_NUMBER
	        '''	
			}
		}	
        
        
        stage ('Upload') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Copy RPMS', script: '''
                    mkdir -p $build_upload_dir/$BUILD_NUMBER
                    shopt -s extglob
					cp ./py-utils/dist/!(*.src.rpm|*.tar.gz) $build_upload_dir/$BUILD_NUMBER
					cp ./statsd-utils/dist/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
                '''
                sh label: 'Repo Creation', script: '''
                    pushd $build_upload_dir/$BUILD_NUMBER
                    yum install -y createrepo
                    createrepo .
                    popd
                '''
                 sh label: 'Tag last_successful', script: '''
                    pushd $build_upload_dir/
                    test -L $build_upload_dir/last_successful && rm -f last_successful
                    ln -s $build_upload_dir/$BUILD_NUMBER last_successful
                    popd
                '''
            }
        }

        stage ('Tag last_successful') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Tag last_successful', script: '''pushd $build_upload_dir/
                    test -L $build_upload_dir/last_successful && rm -f last_successful
                    ln -s $build_upload_dir/$BUILD_NUMBER last_successful
                    popd
                '''
			}
		}

        stage ("Release") {
            when { triggeredBy 'SCMTrigger' }
            steps {
                script { build_stage = env.STAGE_NAME }
				script {
                	def releaseBuild = build job: 'Main Release', propagate: true
				 	env.release_build = releaseBuild.number
                    env.release_build_location = "http://cortx-storage.colo.seagate.com/releases/cortx/github/$branch/$os_version/${env.release_build}"
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
				def recipientProvidersClass = [[$class: 'DevelopersRecipientProvider']]
				if ( manager.build.result.toString() == "FAILURE") {
					toEmail = "shailesh.vaidya@seagate.com,CORTX.Foundation@seagate.com"
					recipientProvidersClass = [[$class: 'DevelopersRecipientProvider'], [$class: 'RequesterRecipientProvider']]
				}
				toEmail = ""
				emailext (
					body: '''${SCRIPT, template="component-email.template"}''',
					mimeType: 'text/html',
				    subject: "[Jenkins Build ${currentBuild.currentResult}] : ${env.JOB_NAME}",
					attachLog: true,
					to: toEmail,
					//recipientProviders: recipientProvidersClass
				)
			}
		}
    }

}