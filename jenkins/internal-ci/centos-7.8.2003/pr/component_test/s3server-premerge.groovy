pipeline {
	 	 
    agent {
		node {
			label 's3-dev-build-7.8.2003'
		}
	}

	options {
		timestamps() 
	        timeout(time: 360, unit: 'MINUTES')
	}

    triggers { 
        cron('30 22 * * *')
    } 

    parameters {  
	    string(name: 'S3_URL', defaultValue: 'https://github.com/Seagate/cortx-s3server', description: 'Repo for S3Server')
        string(name: 'S3_BRANCH', defaultValue: 'main', description: 'Branch for S3Server')     
	}

    environment {
        
        GPR_REPO = "https://github.com/${ghprbGhRepository}"
        S3_URL = "${ghprbGhRepository != null ? GPR_REPO : S3_URL}"
        S3_BRANCH = "${sha1 != null ? sha1 : S3_BRANCH}"

        S3_GPR_REFSEPEC = "+refs/pull/${ghprbPullId}/*:refs/remotes/origin/pr/${ghprbPullId}/*"
        S3_BRANCH_REFSEPEC = "+refs/heads/*:refs/remotes/origin/*"
        S3_PR_REFSEPEC = "${ghprbPullId != null ? S3_GPR_REFSEPEC : S3_BRANCH_REFSEPEC}"
    }
 	
	stages {	
	
            stage('Checkout') {
                steps {
                    script { build_stage = env.STAGE_NAME }
                    step([$class: 'WsCleanup'])
                    checkout([$class: 'GitSCM', branches: [[name: "${S3_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${S3_URL}",  name: 'origin', refspec: "${S3_PR_REFSEPEC}"]]])
                    sh label: 'Script', script: '''
                    set +x
                    echo "---------------------------------------------------------------------------"
                    echo "Building & Running S3 from '${S3_BRANCH}'"
                    echo "---------------------------------------------------------------------------"
                    '''
                }
            } 


            stage ('Dev build & tests') {
                steps {

                    script { build_stage = env.STAGE_NAME }
                    script {
                        sh label: 'Script', script: """
                            git remote -v 
                            rm -rf /root/.seagate_src_cache/
                            rm -rf /root/.cache/bazel/*
                            rm -rf /var/motr/*
                            rm -rf /var/log/seagate/*
                            rm -rf  /root/rpmbuild/*/*
                            git branch
                            echo "Install prerequisite"
                            #yum install python36 -y   # REMOVED TO FIX - https://jts.seagate.com/browse/EOS-18735
                            echo $PWD
                            ./jenkins-build.sh --automate_ansible --generate_support_bundle /jenkins-job-logs --job_id $BUILD_ID
                        """
                    }
                }
            }	

            stage ('S3 RPM build') {
                steps {
                    script { build_stage = env.STAGE_NAME }
                    sh label: 'Script', script: '''
                        echo "Building S3 rpms"
                        rm -rf  /root/rpmbuild/*/*
                        yum clean all
                        yum erase cortx-motr{,-devel} -y -q
                        yum install cortx-motr{,-devel} -y
                        yum erase log4cxx_eos-devel -q -y
                        ./rpms/s3/buildrpm.sh -P $PWD
                        ./rpms/s3iamcli/buildrpm.sh -P $PWD
                        echo "Clean up"
                        rm -rf  /root/rpmbuild/*/*
                    '''
                }
            }	
        }
        
        post {
            always {

                script {
                    echo 'Cleanup Workspace.'
                    deleteDir() /* clean up our workspace */
                    sh label: 'cleanup', script: '''
                    rm -rf /root/.seagate_src_cache/
                    '''

                    if (env.ghprbPullLink) { 
                        env.pr_id = "${ghprbPullLink}"
                    } else {
                        env.branch_name = "${S3_BRANCH}"
                        env.repo_url = "${S3_URL}"
                    }
                    env.build_stage = "${build_stage}"

                    def mailRecipients = "nilesh.govande@seagate.com, basavaraj.kirunge@seagate.com, rajesh.nambiar@seagate.com, ajinkya.dhumal@seagate.com, amit.kumar@seagate.com"
                                        
                    emailext body: '''${SCRIPT, template="mini_prov-email.template"}''',
                    mimeType: 'text/html',
                    recipientProviders: [requestor()], 
                    subject: "[Jenkins] S3AutoPremerge : ${currentBuild.currentResult}, ${JOB_BASE_NAME}#${BUILD_NUMBER}",
                    to: "${mailRecipients}"
                }
            }

            success {
                sh label: 'cleanup', script: '''
                    rm -rf /var/mero/*
                    rm -rf /var/motr/*
                    rm -rf /var/log/seagate/*
                    rm -rf  /root/rpmbuild/*/*
                    rm -rf /root/.cache/bazel/*
                '''
            }
        }	
}
