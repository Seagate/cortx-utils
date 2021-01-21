#!/usr/bin/env groovy
pipeline {
	agent {
		node {
			label 'docker-io-centos-7.8.2003-node'
		}
	}

    parameters {
        string(name: 'branch', defaultValue: 'main', description: 'Branch Name')
    }

	environment {
        version = "2.0.0"
        env = "dev"
		component = "s3server"
        os_version = "centos-7.8.2003"
        pipeline_group = "main"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "${release_dir}/components/github/${pipeline_group}/${os_version}/${env}/${component}"

        // Param hack for initial config
        branch = "${branch != null ? branch : 'main'}"
    }

	options {
		timeout(time: 120, unit: 'MINUTES')
		timestamps()
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
                dir ('s3') {
                    checkout([$class: 'GitSCM', branches: [[name: "*/${branch}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-s3server']]])
                }
            }
        }

		stage("Set Motr Build") {
			stages {			
				stage("Motr Build - Last Successfull") {
					when { not { triggeredBy 'UpstreamCause' } }
					steps {
						script { build_stage = env.STAGE_NAME }
						script {
							sh label: '', script: """
							    yum remove -y cortx-motr{,-devel}
							    yum clean all;rm -rf /var/cache/yum 
							    
							    
								sed '/baseurl/d' /etc/yum.repos.d/motr_current_build.repo
								echo "baseurl=http://cortx-storage.colo.seagate.com/releases/cortx/components/github/stable/$os_version/dev/motr/last_successful/"  >> /etc/yum.repos.d/motr_current_build.repo
								yum-config-manager --disable cortx-C7.7.1908
								yum clean all;rm -rf /var/cache/yum
							"""
						}
					}
				}				
				stage("Motr Build - Current") {
					when { triggeredBy 'UpstreamCause' }
					steps {
						script { build_stage = env.STAGE_NAME }
						script {
							sh label: '', script: """
								sed '/baseurl/d' /etc/yum.repos.d/motr_current_build.repo
								echo "baseurl=http://cortx-storage.colo.seagate.com/releases/cortx/components/github/main/$os_version/dev/motr/current_build/"  >> /etc/yum.repos.d/motr_current_build.repo
								yum-config-manager --disable cortx-C7.7.1908
								yum clean all;rm -rf /var/cache/yum
							"""
						}
					}
				}
			}
		}
        
        stage('Build') {
            steps {
                script { build_stage = env.STAGE_NAME }
                dir ('s3') {	
                    sh label: 'Build s3server RPM', script: '''
                        yum clean all;rm -rf /var/cache/yum
                        export build_number=${BUILD_ID}
                        yum install cortx-motr{,-devel} -y
                        yum erase log4cxx_eos-devel -q -y
                        ./rpms/s3/buildrpm.sh -P $PWD -l
                        
                    '''
                    sh label: 'Build s3iamcli RPM', script: '''
                        export build_number=${BUILD_ID}
                        ./rpms/s3iamcli/buildrpm.sh -P $PWD
                    '''
                }			
            }
        }

        stage ('Upload') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Copy RPMS', script: '''	
                    mkdir -p $build_upload_dir/$BUILD_NUMBER
                    cp /root/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
                    cp /root/rpmbuild/RPMS/noarch/*.rpm $build_upload_dir/$BUILD_NUMBER
                '''
                sh label: 'Repo Creation', script: '''pushd $build_upload_dir/$BUILD_NUMBER
                    rpm -qi createrepo || yum install -y createrepo
                    createrepo .
                    popd
                '''
            }
        }
                            
        stage ('Tag last_successful') {
            when { not { triggeredBy 'UpstreamCause' } }
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Tag last_successful', script: '''pushd $build_upload_dir/
                    test -d $build_upload_dir/last_successful && rm -f last_successful
                    ln -s $build_upload_dir/$BUILD_NUMBER last_successful
                    popd
                '''
            }
        }

        stage ("Release") {
            //when { triggeredBy 'SCMTrigger' }
            when { not { triggeredBy 'UpstreamCause' } }
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

                // TEMP WORKAROUND FOR POLLING ISSUE
                dir ('s3') {
                    checkout([$class: 'GitSCM', branches: [[name: "*/main"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-s3server']]])
                }

				env.release_build = (env.release_build != null) ? env.release_build : "" 
				env.release_build_location = (env.release_build_location != null) ? env.release_build_location : ""
				env.component = (env.component).toUpperCase()
				env.build_stage = "${build_stage}"

                if (currentBuild.rawBuild.getCause (hudson.triggers.SCMTrigger$SCMTriggerCause) ) {
                    def toEmail = "shailesh.vaidya@seagate.com"
                    def recipientProvidersClass = [[$class: 'DevelopersRecipientProvider']]
                    if ( manager.build.result.toString() == "FAILURE") {
                        toEmail = "CORTX.s3@seagate.com"
                        recipientProvidersClass = [[$class: 'DevelopersRecipientProvider'],[$class: 'RequesterRecipientProvider']]
                    }

                    emailext (
                        body: '''${SCRIPT, template="component-email.template"}''',
                        mimeType: 'text/html',
                        subject: "[Jenkins] : ${env.JOB_BASE_NAME} Dev Build ${currentBuild.currentResult}",
                        attachLog: true,
                        to: toEmail,
                        recipientProviders: recipientProvidersClass
                    )
                } else {
                   echo 'Skipping Notification....' 
                }
			}
		}	
    }
}