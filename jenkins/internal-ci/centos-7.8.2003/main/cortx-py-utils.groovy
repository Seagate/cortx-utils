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
		version = "2.0.0"      
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
				./jenkins/build.sh -v $version -b $BUILD_NUMBER
				./statsd-utils/jenkins/build.sh -v $version -b $BUILD_NUMBER
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

				def toEmail = ""
				def recipientProvidersClass = [[$class: 'DevelopersRecipientProvider']]
				if ( manager.build.result.toString() == "FAILURE") {
					toEmail = "shailesh.vaidya@seagate.com,CORTX.Foundation@seagate.com"
					recipientProvidersClass = [[$class: 'DevelopersRecipientProvider'], [$class: 'RequesterRecipientProvider']]
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
