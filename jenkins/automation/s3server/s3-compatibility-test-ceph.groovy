pipeline {
	 	 
    agent {
		node {
            // Agent created with 4GB ram/16GB memory in EOS_SVC_RE1 account 
			label "s3-compatibility-test-ceph-rhev"

            // Use custom workspace for easy troublshooting
            customWorkspace "/root/compatability-test/${INTEGRATION_TYPE}"
		}
	}

	options {
        timeout(time: 240, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm') 
        buildDiscarder(logRotator(numToKeepStr: "30"))
    }

    triggers {
        // Scheduled to run on daily ~ 1-2 AM IST
        cron('H 20 * * *')
    }

    parameters {  
	    string(name: 'S3_URL', defaultValue: 'https://github.com/Seagate/cortx-s3server', description: 'Repo for s3server', trim: true)
        string(name: 'S3_BRANCH', defaultValue: 'main', description: 'Branch for S3Server', trim: true)
        string(name: 'S3_TEST_REPO', defaultValue: 'https://github.com/ceph/s3-tests', description: 's3-test ceph repo', trim: true)
        // we are using specific revision of 'https://github.com/ceph/s3-tests' for our tests  - default
        string(name: 'S3_TEST_REPO_REV', defaultValue: 'b1815c25dcf829b29cf8fc38b6cf83f040e3aa51', description: 's3-test repo revision', trim: true)
        choice(name: 'UPLOAD_TEST_CONF', choices: [ "no", 'yes'], description: 'S3 Integration Type')
        choice(name: 'INTEGRATION_TYPE', choices: [ "ceph"], description: 'S3 Integration Type') 
	}

    environment {
        // This config file used for ceph compatibility tests
        S3_TEST_CONF_FILE = "${INTEGRATION_TYPE}_${BUILD_NUMBER}.conf"
    }
 	
	stages {	

        // Clone s3server source code into workspace
        stage ('Checkout') {
            when { expression { true } }
            steps {
                script {         
                    build_stage = env.STAGE_NAME

                    step([$class: 'WsCleanup'])

                    dir('cortx-s3server') {

                        checkout([$class: 'GitSCM', branches: [[name: "${S3_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[url: '${S3_URL}']]])
                        env.S3_COMMIT_ID = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                    }
                }
            }
        }

        // Cleanup previous build and starts s3server build on latest source code
        stage ('Build ') {
            when { expression {  params.UPLOAD_TEST_CONF != 'yes' } }
            steps {
                script {
                    build_stage = env.STAGE_NAME

                    dir('cortx-s3server') {

                        // previous build, support bundle cleanup
                        sh label: 'cleanup', script: """
                            rm -rf /root/.seagate_src_cache/
                            rm -rf /root/.cache/bazel/*
                            rm -rf /var/motr/*
                            rm -rf /var/log/seagate/*
                            rm -rf  /root/rpmbuild/*/*

                            sh scripts/s3-logrotate/s3supportbundlefilerollover.sh
                        """

                        // Execute s3server build (skip tests)
                        sh label: 'build', script: """
                            ./jenkins-build.sh --automate_ansible --skip_tests || true
                        """

                        // Start s3server for testing
                        sh label: 'start', script: """
                            third_party/motr/m0t1fs/../motr/st/utils/motr_services.sh stop || true
                            systemctl stop s3authserver || true
                            ./dev-stops3.sh || true

                            systemctl restart slapd || true
                            systemctl restart haproxy || true
                            third_party/motr/m0t1fs/../motr/st/utils/motr_services.sh start || true
                            systemctl restart s3authserver || true
                            ./dev-starts3.sh || true
                        """
                    }         
                }
            }
        }	

        // If we want to execute test against any prebuild server (eg: aws)
        stage ('Upload Test Config') {
            when { expression {  params.UPLOAD_TEST_CONF == 'yes' } }
            agent { label 'master' }
            steps {          
                script { build_stage = env.STAGE_NAME }
                script {
                    def s3TestConfig = input message: 'Upload S3 Test Config', parameters: [file(name: "s3_test_conf", description: 'Upload only s3test conf file')]
                    writeFile(file: "${S3_TEST_CONF_FILE}", text: s3TestConfig.readToString())
                    stash name: "s3_test_conf", includes: "${S3_TEST_CONF_FILE}"
                }
            }
        }

        // Update test config for s3server auth credentials
        stage ('Update Test Config') {
            when { expression { true } }      
            steps {
                script { build_stage = env.STAGE_NAME }
                
                script {
                    if ( "${UPLOAD_TEST_CONF}" == "yes" ) {

                        unstash "s3_test_conf"
                    
                    } else {
                        
                        dir('cortx-re') {
                            checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '*/main']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]]
                        }
                                        
                        sh label: 'run compatibility test', script: '''
                            #set +x
                            # Get Ldap credentials
                            LDAP_USR="sgiamadmin"
                            LDAP_PWD=$(cat ~/.s3_ldap_cred_cache.conf | grep "ldap_admin_pwd" | cut -d= -f2 | xargs)

                            S3_MAIN_USER="s3-test-main"
                            S3_EXT_USER="s3-test-ext"
                            S3_TNT_USER="s3-test-tnt"

                            chmod +x cortx-re/scripts/automation/s3-test/create_s3_account.sh
                            ./cortx-re/scripts/automation/s3-test/create_s3_account.sh ${S3_MAIN_USER}_${BUILD_NUMBER} ${S3_MAIN_USER}_${BUILD_NUMBER}@seagate.com $LDAP_USR $LDAP_PWD >> s3_account_main.txt
                            ./cortx-re/scripts/automation/s3-test/create_s3_account.sh ${S3_EXT_USER}_${BUILD_NUMBER} ${S3_EXT_USER}_${BUILD_NUMBER}@seagate.com $LDAP_USR $LDAP_PWD >> s3_account_alt.txt
                            ./cortx-re/scripts/automation/s3-test/create_s3_account.sh ${S3_TNT_USER}_${BUILD_NUMBER} ${S3_TNT_USER}_${BUILD_NUMBER}@seagate.com $LDAP_USR $LDAP_PWD >> s3_account_tnt.txt

                            # Set Main & Ext user cred in environment variable. This is required in config file
                            S3_MAIN_USER_NAME="${S3_MAIN_USER}_${BUILD_NUMBER}"
                            S3_MAIN_USER_ID=$(cat s3_account_main.txt | grep "AccountId" | cut -d, -f2 | cut -d= -f2 | xargs)
                            S3_MAIN_ACCESS_KEY=$(cat s3_account_main.txt | grep "AccountId" | cut -d, -f4 | cut -d= -f2 | xargs)
                            S3_MAIN_SECRET_KEY=$(cat s3_account_main.txt | grep "AccountId" | cut -d, -f5 | cut -d= -f2 | xargs)
                            S3_ALT_USER_ID=$(cat s3_account_alt.txt | grep "AccountId" | cut -d, -f2 | cut -d= -f2 | xargs)
                            S3_ALT_ACCESS_KEY=$(cat s3_account_alt.txt | grep "AccountId" | cut -d, -f4 | cut -d= -f2 | xargs)
                            S3_ALT_SECRET_KEY=$(cat s3_account_alt.txt | grep "AccountId" | cut -d, -f5 | cut -d= -f2 | xargs)

                            S3_TNT_USER_ID=$(cat s3_account_alt.txt | grep "AccountId" | cut -d, -f2 | cut -d= -f2 | xargs)
                            S3_TNT_ACCESS_KEY=$(cat s3_account_alt.txt | grep "AccountId" | cut -d, -f4 | cut -d= -f2 | xargs)
                            S3_TNT_SECRET_KEY=$(cat s3_account_alt.txt | grep "AccountId" | cut -d, -f5 | cut -d= -f2 | xargs)

                            cp cortx-s3server/scripts/compatibility-test/${INTEGRATION_TYPE}/${INTEGRATION_TYPE}.conf ${S3_TEST_CONF_FILE}
                            sed -i "s#<S3_MAIN_USER_NAME>#${S3_MAIN_USER_NAME}#;s#<S3_MAIN_USER_ID>#${S3_MAIN_USER_ID}#;s#<S3_MAIN_ACCESS_KEY>#${S3_MAIN_ACCESS_KEY}#;s#<S3_MAIN_SECRET_KEY>#${S3_MAIN_SECRET_KEY}#g;" ${S3_TEST_CONF_FILE}
                            sed -i "s#<S3_ALT_USER_ID>#${S3_ALT_USER_ID}#; s#<S3_ALT_ACCESS_KEY>#${S3_ALT_ACCESS_KEY}#; s#<S3_ALT_SECRET_KEY>#${S3_ALT_SECRET_KEY}#g;" ${S3_TEST_CONF_FILE}
                            sed -i "s#<S3_TNT_USER_ID>#${S3_TNT_USER_ID}#; s#<S3_TNT_ACCESS_KEY>#${S3_TNT_ACCESS_KEY}#; s#<S3_TNT_SECRET_KEY>#${S3_TNT_SECRET_KEY}#g;" ${S3_TEST_CONF_FILE}

                        '''
                    }
                }
            }
        }

        // Execute s3 server compatibility tests
        stage ('Run S3 Compatibility Test') {

            when { expression { true } }

            steps {
                
                script { build_stage = env.STAGE_NAME }
                  
                sh label: 'run compatibility test', script: '''
                   
                    echo "---------------------------------"
                    echo ""
                    chmod +x cortx-s3server/scripts/compatibility-test/run-test.sh
                    sh cortx-s3server/scripts/compatibility-test/run-test.sh -c="${S3_TEST_CONF_FILE}" -i="${INTEGRATION_TYPE}" -tr="${S3_TEST_REPO}" -trr="${S3_TEST_REPO_REV}"
                    echo ""
                    echo "---------------------------------"
                '''
            }
        }

        // Generate support bundle on post test
        stage ('Generate Support Bundle ') {
            when { expression { true } }
            steps {
                script {
                    build_stage = env.STAGE_NAME

                    sh label: 'build', script: '''
                        echo "Creating support bundle in /jenkins-job-logs/" 
                        cd /opt/seagate/cortx/s3/scripts/
                        ./s3_bundle_generate.sh bundle_$(hostname)_`date +%d-%m-%y` /jenkins-job-logs
                        ls /jenkins-job-logs/s3 ;
                    '''   
                }
            }
        }		
    }
        
    post {
        
        always {

            script {
                
                // Archive all test report artifacts
                archiveArtifacts artifacts: "*.txt, ${S3_TEST_CONF_FILE}, reports/*", onlyIfSuccessful: false, allowEmptyArchive: true  

                // Add test result to Jenkins Junit report
                junit testResults: 'reports/*.xml', testDataPublishers: [[$class: 'AttachmentPublisher']]  

                def mailRecipients = "nilesh.govande@seagate.com, basavaraj.kirunge@seagate.com, rajesh.nambiar@seagate.com, ajinkya.dhumal@seagate.com, amit.kumar@seagate.com, shazia.ahmad@seagate.com"
                    
                emailext body: '''${SCRIPT, template="s3-comp-test-email.template"}''',
                mimeType: 'text/html',
                recipientProviders: [requestor()], 
                subject: "[Jenkins] S3Ceph : ${currentBuild.currentResult}, ${JOB_BASE_NAME}#${BUILD_NUMBER}",
                to: "${mailRecipients}"
            }
        }
    }	
}