pipeline {

    agent {
        node {
            label 'motr-remote-controller-hw'
        }
    }

    parameters {
        string(name: 'MOTR_URL', defaultValue: 'https://github.com/gowthamchinna/cortx-motr', description: 'Repo for Motr')
        string(name: 'MOTR_BRANCH', defaultValue: 'main', description: 'Branch for Motr')  
    }

    options {
		timestamps ()
        timeout(time: 10, unit: 'HOURS')
	}

    environment{
    
        GPR_REPO = "https://github.com/${ghprbGhRepository}"
        MOTR_URL = "${ghprbGhRepository != null ? GPR_REPO : MOTR_URL}"
        MOTR_BRANCH = "${sha1 != null ? sha1 : MOTR_BRANCH}"

        MOTR_GPR_REFSEPEC = "+refs/pull/${ghprbPullId}/*:refs/remotes/origin/pr/${ghprbPullId}/*"
        MOTR_BRANCH_REFSEPEC = "+refs/heads/*:refs/remotes/origin/*"
        MOTR_PR_REFSEPEC = "${ghprbPullId != null ? MOTR_GPR_REFSEPEC : MOTR_BRANCH_REFSEPEC}"

    }

	stages {

        stage('Trigger VM Test') {
            when { expression { false } }
            steps{
                build job: '../Motr/Motr-PR-Test-VM', propagate: false, wait: false, parameters: [string(name: 'MOTR_URL', value: "${MOTR_URL}"), string(name: 'MOTR_BRANCH', value: "${MOTR_BRANCH}"), , string(name: 'MOTR_REFSEPEC', value: "${MOTR_PR_REFSEPEC}")]
            }
        }

        stage('Checkout') {
            when { expression { true } }
            steps {
                cleanWs()
                dir('motr') {
                    checkout([$class: 'GitSCM', branches: [[name: "*/${MOTR_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${MOTR_URL}", name: 'origin', refspec: "${MOTR_PR_REFSEPEC}"]]])
                }
                dir('xperior') {
                    git credentialsId: 'cortx-admin-github', url: "https://github.com/Seagate/xperior.git", branch: "main"
                }
                dir('xperior-perl-libs') {
                    git credentialsId: 'cortx-admin-github', url: "https://github.com/Seagate/xperior-perl-libs.git", branch: "main"
                }
                dir('seagate-ci') {
                    git credentialsId: 'cortx-admin-github', url: "https://github.com/Seagate/seagate-ci", branch: "main"
                }
                dir('seagate-eng-tools') {
                    git credentialsId: 'cortx-admin-github', url: "https://github.com/Seagate/seagate-eng-tools.git", branch: "main"
                }
            }
        }
        stage('Static Code Analysis') {
            when { expression { true } }
            steps {
                script {

                    sh  label: 'run cppcheck', script:'''
                        mkdir -p html
                        /opt/perlbrew/perls/perl-5.22.0/bin/perl seagate-eng-tools/scripts/build_support/cppcheck.pl --src=motr  --debug --maxconfig=2 --jenkins --xmlreport=diff.xml --cfgfile=seagate-eng-tools/jenkins/build/motr_cppcheck.yaml  --htmldir=html --reporturl="${BUILD_URL}/CppCheck_Report/"
                    '''
                    sh  label: 'get cppcheck result', script:'''
                        no_warning=$(cat html/index.html | grep "total<br/><br/>" | tr -dc '0-9')
                        sca_result="Cppcheck: No new warnings found"
                        if [ "$no_warning" != "0" ]; then 
                            sca_result="Cppcheck: Found $no_warning new warning(s)"
                        fi
                        echo $sca_result > cppcheck_Result
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'html/*.*', fingerprint: true
                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: true, reportDir: 'html', reportFiles: 'index.html', reportName: 'CppCheck Report', reportTitles: ''])
                    //githubNotify context: 'premerge-test', description: "Build finished", targetUrl: "${BUILD_URL}/testReport",  status: 'SUCCESS'
                    
                    githubNotify account: 'gowthamchinna', context: 'premerge-test', credentialsId: 'gowthamchinna',
                                description: 'This is an example', repo: 'acceptance-test-harness', sha: "${sha}"
                                , status: 'SUCCESS', targetUrl: '${BUILD_URL}/testReport'
                }
            }
        }
        stage('Run Test') {
            when { expression { false } }
            steps {
                script {
                    sh '''
                        set -ae
                        set
                        WD=$(pwd)
                        hostname
                        id
                        ls
                        export DO_MOTR_BUILD=yes
                        export MOTR_REFSPEC=""
                        export TESTDIR=motr/.xperior/testds/
                        export XPERIOR="${WD}/xperior"
                        export ITD="${WD}/seagate-ci/xperior"
                        export XPLIB="${WD}/xperior-perl-libs/extlib/lib/perl5"
                        export PERL5LIB="${XPERIOR}/mongo/lib:${XPERIOR}/lib:${ITD}/lib:${XPLIB}/"
                        export PERL_HOME="/opt/perlbrew/perls/perl-5.22.0/"
                        export PATH="${PERL_HOME}/bin/:$PATH:/sbin/:/usr/sbin/"
                        export RWORKDIR='motr/motr_test_github_workdir/workdir'
                        export IPMIDRV=lan
                        export BUILDDIR="/root/${RWORKDIR}"
                        export XPEXCLUDELIST=""
                        export UPLOADTOBOARD=
                        export PRERUN_REBOOT=yes

                        ${PERL_HOME}/bin/perl "${ITD}/contrib/run_motr_single_test.pl"
                    '''
                }
            }
            post {
                always {
                    script {
                        archiveArtifacts artifacts: 'workdir/**/*.*, build*.*, artifacts/*.*', fingerprint: true, allowEmptyArchive: true
                        summary = junit testResults: '**/junit/*.junit', allowEmptyResults : true, testDataPublishers: [[$class: 'AttachmentPublisher']]     

                        if ("${ghprbPullId}") {
                            try {
                                postGithubComment(summary, readFile('cppcheck_Result').trim())
                            } catch (err) {
                                echo "Failed to update Github PR Comment ${err}"
                            }
                        }
                        
                        cleanWs()
                        
                        setBuildStatus("Build failed", "FAILURE", "${MOTR_URL}");
                        //githubNotify context: 'premerge-test', description: "\n *Test Summary* - ${summary.totalCount}, Failures: ${summary.failCount}, Skipped: ${summary.skipCount}, Passed: ${summary.passCount}", targetUrl: "${BUILD_URL}/testReport",  status: 'SUCCESS'
                        //githubNotify context: 'premerge-test', description: "Build finished", targetUrl: "${BUILD_URL}/testReport",  status: 'SUCCESS'

                    }                            
                }
            }
        }    	
    }
}

@NonCPS
def postGithubComment(junitSummary, cppcheckSummary) {
    def githubComment="<h1>Jenkins CI Result : <a href=\'${BUILD_URL}\'>${env.JOB_BASE_NAME}#${env.BUILD_ID}</a></h1>"
    hudson.tasks.test.AbstractTestResultAction testResultAction = currentBuild.rawBuild.getAction(hudson.tasks.test.AbstractTestResultAction.class)
    if (testResultAction != null) {
        def testURL = "${BUILD_URL}/testReport/junit"
        def passedTest = testResultAction.getPassedTests().collect { "<a href=\'${testURL}/${it.className.replaceAll('\\.','/')}\' target='_blank'>${it.className.replaceAll('\\.','/')}</a>" }.join("</br>")
        def failedTest = testResultAction.getFailedTests().collect { "<a href=\'${testURL}/${it.className.replaceAll('\\.','/')}\' target='_blank'>${it.className.replaceAll('\\.','/')}</a>"  }.join("</br>")
        def skippedTest = testResultAction.getSkippedTests().collect { "<a href=\'${testURL}/${it.className.replaceAll('\\.','/')}\' target='_blank'>${it.className.replaceAll('\\.','/')}</a>" }.join("</br>")
      
        githubComment+="<h2>Motr Test Summary</h2><table><tr><th>Test Result</th><th>Count</th><th>Info</tr>"
        githubComment+="<tr><td>:x:Failed</td><td>${junitSummary.failCount}</td><td><details><summary>:file_folder:</summary><p>${failedTest}</p></details></td></tr>"
        githubComment+="<tr><td>:checkered_flag:Skipped</td><td>${junitSummary.skipCount}</td><td><details><summary>:file_folder:</summary><p>${skippedTest}</p></details></td></tr>"
        githubComment+="<tr><td>:heavy_check_mark:Passed</td><td>${junitSummary.passCount}</td><td><details><summary>:file_folder:</summary><p>${passedTest}</p></details></td></tr>"
        githubComment+="<tr><td>Total</td><td>${junitSummary.totalCount}</td><td><a href=\'${testURL}\'>:link:</a></td></tr></table>"

        if (cppcheckSummary) {
            githubComment+="<h2> CppCheck Summary</h2><p> &emsp;&emsp;&emsp;${cppcheckSummary} :thumbsup:</p>"
        }
        githubAPIAddComments(githubComment)
    }
}

// method to call gitub post comment api to add comments
def githubAPIAddComments(text_pr) {

    withCredentials([usernamePassword(credentialsId: "cortx-admin-github", passwordVariable: 'GITHUB_TOKEN', usernameVariable: 'USER')]) {
        sh """
            curl -s -H \"Authorization: token ${GITHUB_TOKEN}\" -X POST -d '{"body":"${text_pr}"}' \"https://api.github.com/repos/${ghprbGhRepository}/issues/${ghprbPullId}/comments\"
        """
    }
}

def setBuildStatus(String message, String state, String context, String sha) {
    step([
        $class: "GitHubCommitStatusSetter",
        reposSource: [$class: "ManuallyEnteredRepositorySource", url: "${MOTR_URL}"],
        contextSource: [$class: "ManuallyEnteredCommitContextSource", context: context],
        errorHandlers: [[$class: "ChangingBuildStatusErrorHandler", result: "UNSTABLE"]],
        commitShaSource: [$class: "ManuallyEnteredShaSource", sha: sha ],
        statusBackrefSource: [$class: "ManuallyEnteredBackrefSource", backref: "${BUILD_URL}flowGraphTable/"],
        statusResultSource: [$class: "ConditionalStatusResultSource", results: [[$class: "AnyBuildResult", message: message, state: state]] ]
    ]);
}