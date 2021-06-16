#!/usr/bin/env groovy
pipeline {
	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}
	
	triggers {
        pollSCM '*/5 * * * *'
    }
	
	environment { 
		version = "2.0.0"     
        env = "dev"
		component = "csm-agent"
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

		stage('Checkout') {
			steps {
				script { build_stage = env.STAGE_NAME }

				dir ('cortx-csm-agent') {
					checkout([$class: 'GitSCM', branches: [[name: "*/${branch}"]], doGenerateSubmoduleConfigurations: false,  extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-manager']]])
				}
			}
		}
		
		stage('Install Dependencies') {
			steps {
				script { build_stage = env.STAGE_NAME }

				dir ('cortx-re') {
					checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: 'main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', noTags: true, reference: '', shallow: true]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]]
				}

				sh label: '', script: '''
				#Use main branch for cortx-py-utils
				sed -i 's/stable/main/'  /etc/yum.repos.d/cortx.repo
				yum clean all && rm -rf /var/cache/yum

				# Install cortx-prereq package
					pip3 uninstall pip -y && yum install python3-pip -y && ln -s /usr/bin/pip3 /usr/local/bin/pip3
					sh ./cortx-re/scripts/third-party-rpm/install-cortx-prereq.sh
					yum clean all && rm -rf /var/cache/yum

				# Install pyinstaller	
				pip3.6 install  pyinstaller==3.5
				'''
			}
		}	
		
		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				// Exclude return code check for csm_setup and csm_test
				sh label: 'Build', script: '''
					BUILD=$(git rev-parse --short HEAD)
					echo "Executing build script"
					echo "Python:$(python --version)"
					./cortx-csm-agent/cicd/build.sh -v $version -b $BUILD_NUMBER -t
				'''	
			}
		}
		
		stage ('Upload') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					mkdir -p $build_upload_dir/$BUILD_NUMBER
					cp ./cortx-csm-agent/dist/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
				'''
				sh label: 'Repo Creation', script: '''pushd $build_upload_dir/$BUILD_NUMBER
					rpm -qi createrepo || yum install -y createrepo
					createrepo .
					popd
				'''
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
						//} 
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

				def toEmail = ""
				def recipientProvidersClass = [[$class: 'DevelopersRecipientProvider'], [$class: 'RequesterRecipientProvider']]
				if( manager.build.result.toString() == "FAILURE" ) {
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