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
		component = "hare"
        os_version = "centos-7.8.2003"
		pipeline_group = "main"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "${release_dir}/components/github/${pipeline_group}/${os_version}/${env}/${component}"

		// Param hack for initial config
        branch = "${branch != null ? branch : 'main'}"
    }
	
	options {
		timeout(time: 60, unit: 'MINUTES')
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
			    script {
    			    retry(2) {
                        try {
            				script { build_stage = env.STAGE_NAME }
            				dir ('hare') {
            					checkout([$class: 'GitSCM', branches: [[name: "*/${branch}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false,  timeout: 5], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-hare.git']]])
            				}
                        } catch (err) {
                            error "Checkout Timeout.....${err}"
                        }
    			    }
			    }
			}
		}

        stage("Set Motr Build") {
			stages {			
				stage("Motr Build - Stable Build") {
					when { not { triggeredBy 'UpstreamCause' } }
					steps {
						script { build_stage = env.STAGE_NAME }
						script {
							sh label: '', script: '''
								sed '/baseurl/d' /etc/yum.repos.d/motr_current_build.repo
								echo "baseurl=http://cortx-storage.colo.seagate.com/releases/cortx/components/github/stable/$os_version/$env/motr/last_successful/"  >> /etc/yum.repos.d/motr_current_build.repo
								yum-config-manager --disable cortx-C7.7.1908
								yum clean all;rm -rf /var/cache/yum
							'''
						}
					}
				}				
				stage("Motr Build - Main Build") {
					when { triggeredBy 'UpstreamCause' }
					steps {
						script { build_stage = env.STAGE_NAME }
						script {
							sh label: '', script: '''
								sed '/baseurl/d' /etc/yum.repos.d/motr_current_build.repo
								echo "baseurl=http://cortx-storage.colo.seagate.com/releases/cortx/components/github/main/$os_version/$env/motr/current_build/"  >> /etc/yum.repos.d/motr_current_build.repo
								yum-config-manager --disable cortx-C7.7.1908
								yum clean all;rm -rf /var/cache/yum
							'''
						}
					}
				}
			}
        }
	
		stage('Install Dependencies') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: '', script: '''
					rm -f /etc/yum.repos.d/eos_7.7.1908.repo
					yum clean all
					rm -rf /var/cache/yum
					yum install cortx-motr{,-devel} -y
				'''
			}
		}

		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Build', returnStatus: true, script: '''
					set -xe
					pushd $component
					echo "Executing build script"
					export build_number=${BUILD_ID}
					make rpm
					popd
				'''	
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
            when { not { triggeredBy 'UpstreamCause' } }
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
				try {
				   dir('hare') {
    					checkout([$class: 'GitSCM', branches: [[name: "*/main"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: false, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-hare.git']]])
    				}
                } catch (err) {
                    echo "Checkout Timeout"
                }
                
				env.release_build = (env.release_build != null) ? env.release_build : "" 
				env.release_build_location = (env.release_build_location != null) ? env.release_build_location : ""
				env.component = (env.component).toUpperCase()
				env.build_stage = "${build_stage}"

			
				def toEmail = ""
				def recipientProvidersClass = [[$class: 'DevelopersRecipientProvider']]
				if ( manager.build.result.toString() == "FAILURE") {
					toEmail = "CORTX.Hare@seagate.com,shailesh.vaidya@seagate.com"
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