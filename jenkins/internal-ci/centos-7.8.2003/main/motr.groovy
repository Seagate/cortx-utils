#!/usr/bin/env groovy
pipeline {
	agent {
		node {
			label 'docker-motr-centos-7.8.2003-node'
		}
	}

	parameters {
        string(name: 'branch', defaultValue: 'main', description: 'Branch Name')
    }
		
	environment {
        version = "2.0.0"    
        env = "dev"
		component = "motr"
        os_version = "centos-7.8.2003"
		pipeline_group = "main"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "${release_dir}/components/github/${pipeline_group}/${os_version}/${env}/${component}"

        // Dependent component job build
        build_upload_dir_s3 = "$release_dir/components/github/${pipeline_group}/${os_version}/${env}/s3server"
        build_upload_dir_hare = "$release_dir/components/github/${pipeline_group}/${os_version}/${env}/hare"

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
				dir ('motr') {
			        checkout([$class: 'GitSCM', branches: [[name: "*/${branch}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-motr']]])
                }
			}
		}
	
    	stage('Install Dependencies') {
		    steps {
				script { build_stage = env.STAGE_NAME }
				dir ('motr') {	
					sh label: '', script: '''
                        export build_number=${BUILD_ID}
						kernel_src=$(ls -1rd /lib/modules/*/build | head -n1)
						cp cortx-motr.spec.in cortx-motr.spec
						sed -i 's/@.*@/111/g' cortx-motr.spec
						yum-builddep -y cortx-motr.spec
					'''	
				}
			}
		}

		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				dir ('motr') {	
					sh label: '', script: '''
						rm -rf /root/rpmbuild/RPMS/x86_64/*.rpm
						KERNEL=/lib/modules/$(yum list installed kernel | tail -n1 | awk '{ print $2 }').x86_64/build
						./autogen.sh
						./configure --with-linux=$KERNEL
						export build_number=${BUILD_ID}
						make rpms
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
				'''
                sh label: 'Repo Creation', script: '''pushd $build_upload_dir/$BUILD_NUMBER
					rpm -qi createrepo || yum install -y createrepo
					createrepo .
					popd
				'''
			}
		}
		
		stage ('Set Current Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Tag last_successful', script: '''
					pushd $build_upload_dir/
					test -d $build_upload_dir/current_build && rm -f current_build
					ln -s $build_upload_dir/$BUILD_NUMBER current_build
					popd
				'''
			}
		}
		
		stage ("Trigger Downstream Jobs") {
			parallel {
				stage ("build S3Server") {
					steps {
						script { build_stage = env.STAGE_NAME }
                        script {
                                try {
                                    def s3Build = build job: 'S3server', wait: true, parameters: [string(name: 'branch', value: "stable")]
							        env.S3_BUILD_NUMBER = s3Build.number
                                } catch (err) {
                                    build_stage = env.STAGE_NAME
                                    error "Failed to Build S3Server"
                                }
						}
					}
				}
					        
		        stage ("build Hare") {
					steps {
						script { build_stage = env.STAGE_NAME }
                        script {
                            try {
							    def hareBuild = build job: 'Hare', wait: true, parameters: [string(name: 'branch', value: "stable")]
							    env.HARE_BUILD_NUMBER = hareBuild.number
                            } catch (err) {
                                build_stage = env.STAGE_NAME
                                error "Failed to Build Hare"
                            }
						}
					}
				}
			}	
		}
	
		stage ('Tag last_successful') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Tag last_successful', script: '''pushd $build_upload_dir/
					test -d $build_upload_dir/last_successful && rm -f last_successful
					ln -s $build_upload_dir/$BUILD_NUMBER last_successful
					popd
				'''
                sh label: 'Tag last_successful for dep component', script: '''
					# Hare Build 
                    test -d $build_upload_dir_hare/last_successful && rm -f $build_upload_dir_hare/last_successful
					ln -s $build_upload_dir_hare/$HARE_BUILD_NUMBER $build_upload_dir_hare/last_successful

                    # S3Server Build
                    test -d $build_upload_dir_s3/last_successful && rm -f $build_upload_dir_s3/last_successful
					ln -s $build_upload_dir_s3/$S3_BUILD_NUMBER $build_upload_dir_s3/last_successful
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
				def recipientProvidersClass = [[$class: 'DevelopersRecipientProvider']]
				if ( manager.build.result.toString() == "FAILURE") {
					toEmail = ""
					recipientProvidersClass = [[$class: 'DevelopersRecipientProvider'], [$class: 'RequesterRecipientProvider']]
				}
                toEmail = ""
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
