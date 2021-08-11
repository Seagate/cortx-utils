#!/usr/bin/env groovy
pipeline {
    agent {
		node {
			label 'docker-io-centos-7.8.2003-node'
		}
	}

	triggers {
        pollSCM '*/5 * * * *'
    }
    
    environment {
		version = "2.0.0"
        env = "dev"
		component = "hare"
        branch = "main"
        os_version = "centos-7.8.2003"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "$release_dir/components/github/$branch/$os_version/$env/$component"
    }
	
	options {
		timeout(time: 120, unit: 'MINUTES')
		timestamps()
        ansiColor('xterm') 
		disableConcurrentBuilds()  
	}

	stages {
		stage('Checkout') {
			steps {
				script { build_stage = env.STAGE_NAME }
				dir ('hare') {
					checkout([$class: 'GitSCM', branches: [[name: 'main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', noTags: true, reference: '', shallow: true], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', shallow: true, trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', refspec: '+refs/heads/main:refs/remotes/origin/main', url: 'https://github.com/Seagate/cortx-hare']]])
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
							sh label: '', script: '''
								sed -i '/baseurl/d' /etc/yum.repos.d/motr_current_build.repo
								echo "baseurl=http://cortx-storage.colo.seagate.com/releases/cortx/components/github/$branch/$os_version/dev/motr/last_successful/"  >> /etc/yum.repos.d/motr_current_build.repo
								# Install cortx-py-utils from main branch
								sed -i 's/stable/main/'  /etc/yum.repos.d/cortx.repo
								yum clean all;rm -rf /var/cache/yum
							'''
						}
					}
				}				
				stage("Motr Build - Current") {
					when { triggeredBy 'UpstreamCause' }
					steps {
						script { build_stage = env.STAGE_NAME }
						script {
							sh label: '', script: '''
								sed -i '/baseurl/d' /etc/yum.repos.d/motr_current_build.repo
								echo "baseurl=http://cortx-storage.colo.seagate.com/releases/cortx/components/github/$branch/$os_version/dev/motr/current_build/"  >> /etc/yum.repos.d/motr_current_build.repo
								# Install cortx-py-utils from main branch
								sed -i 's/stable/main/'  /etc/yum.repos.d/cortx.repo
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
					yum erase python36-PyYAML -y
					cat <<EOF >>/etc/pip.conf
[global]
timeout: 60
index-url: http://cortx-storage.colo.seagate.com/releases/cortx/third-party-deps/python-deps/python-packages-2.0.0-latest/
trusted-host: cortx-storage.colo.seagate.com
EOF
					pip3 install -r https://raw.githubusercontent.com/Seagate/cortx-utils/$branch/py-utils/python_requirements.txt
					pip3 install -r https://raw.githubusercontent.com/Seagate/cortx-utils/$branch/py-utils/python_requirements.ext.txt
					rm -rf /etc/pip.conf
                '''

				sh label: '', script: '''
					yum install cortx-py-utils cortx-motr{,-devel} -y
				'''
			}
		}

		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Build', script: '''
					set -xe
					pushd $component
					echo "Executing build script"
					export build_number=${BUILD_ID}
					make VERSION=$version rpm
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
            steps {
                script { build_stage = env.STAGE_NAME }
				script {
                	def releaseBuild = build job: 'Main Release', propagate: true
				 	env.release_build = releaseBuild.number
                    env.release_build_location = "http://cortx-storage.colo.seagate.com/releases/cortx/github/$branch/$os_version/${env.release_build}"
				}
            }
        }
        stage('Update Jira') {
                when { expression { return env.release_build != null } }
	                steps {
                        script { build_stage=env.STAGE_NAME }
				script {
			        	def jiraIssues = jiraIssueSelector(issueSelector: [$class: 'DefaultIssueSelector'])
					jiraIssues.each { issue ->
						def author =  getAuthor(issue)
						jiraAddComment(
							idOrKey: issue,
							site: "SEAGATE_JIRA",
							comment: "{panel:bgColor=#c1c7d0}"+
								"h2. ${component} - ${branch} branch build pipeline SUCCESS\n"+
								"h3. Build Info:  \n"+
									author+
										"* Component Build  :  ${BUILD_NUMBER} \n"+
										"* Release Build    :  ${release_build}  \n\n  "+
								"h3. Artifact Location  :  \n"+
									 "*  "+"${release_build_location} "+"\n"+
									 "{panel}",
							failOnError: false,
							auditLog: false
						)
						//def jiraFileds = jiraGetIssue idOrKey: issue, site: "SEAGATE_JIRA", failOnError: false
						//if(jiraFileds.data != null){
						//def labels_data =  jiraFileds.data.fields.labels + "cortx_stable_b${release_build}"
						//jiraEditIssue idOrKey: issue, issue: [fields: [ labels: labels_data ]], site: "SEAGATE_JIRA", failOnError: false
						// }
					}
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

                // VM Deployment 
                env.vm_deployment = (env.deployVMURL != null) ? env.deployVMURL : "" 
                if ( env.deployVMStatus != null && env.deployVMStatus != "SUCCESS" && manager.build.result.toString() == "SUCCESS" ) {
                    manager.buildUnstable()
                }

				def toEmail = ""
				def recipientProvidersClass = [[$class: 'DevelopersRecipientProvider']]
				if( manager.build.result.toString() == "FAILURE" ) {
					toEmail = "CORTX.Hare@seagate.com,shailesh.vaidya@seagate.com"
					recipientProvidersClass = [[$class: 'DevelopersRecipientProvider'],[$class: 'RequesterRecipientProvider']]
				}

				emailext (
					body: '''${SCRIPT, template="component-email-dev.template"}''',
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

@NonCPS
def getAuthor(issue) {

    def changeLogSets = currentBuild.rawBuild.changeSets
    def author= ""
    def response = ""
    // Grab build information
    for (int i = 0; i < changeLogSets.size(); i++){
        def entries = changeLogSets[i].items
        for (int j = 0; j < entries.length; j++) {
            def entry = entries[j]
            if((entry.msg).contains(issue)){
                author = entry.author
            }
        }
    }
    response = "* Author: "+author+"\n"
    return response
}
