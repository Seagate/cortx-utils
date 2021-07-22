#!/usr/bin/env groovy
pipeline {
    agent {
        node {
            label "docker-${os_version}-node"
        }
    }
    
    triggers {
        pollSCM '*/5 * * * *'
    }
    
    environment { 
        version = "2.0.0"     
        env = "dev"
        component = "csm-agent"
        release_dir = "/mnt/bigstorage/releases/cortx"
        release_tag = "last_successful_prod"
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
                    checkout([$class: 'GitSCM', branches: [[name: "${branch}"]], doGenerateSubmoduleConfigurations: false,  extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-manager']]])
                }
                dir('seagate-ldr') {
                    checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/seagate-ldr.git']]])
                }
                dir ('cortx-re') {
                    checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: 'main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', noTags: true, reference: '', shallow: true]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]]
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script { build_stage = env.STAGE_NAME }

                sh label: 'Install cortx-prereq package', script: """
                    pip3 uninstall pip -y && yum reinstall python3-pip -y && ln -s /usr/bin/pip3 /usr/local/bin/pip3
                    sh ./cortx-re/scripts/third-party-rpm/install-cortx-prereq.sh
                """
                
                sh label: 'Configure yum repositories', script: """
                    yum-config-manager --add-repo=http://cortx-storage.colo.seagate.com/releases/cortx/github/$branch/$os_version/$release_tag/cortx_iso/
                    yum-config-manager --save --setopt=cortx-storage*.gpgcheck=1 cortx-storage* && yum-config-manager --save --setopt=cortx-storage*.gpgcheck=0 cortx-storage*
                    yum clean all && rm -rf /var/cache/yum
                """

                sh label: 'Install pyinstaller', script: """
                        pip3.6 install  pyinstaller==3.5
                """
            }
        }        
        
        stage('Build') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Build', script: '''
                pushd cortx-csm-agent
                    BUILD=$(git rev-parse --short HEAD)
                    echo "Executing build script"
                    echo "Python:$(python --version)"
                    ./cicd/build.sh -v $version -b $BUILD_NUMBER -t -n ldr -l $WORKSPACE/seagate-ldr
                popd    
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
                    def releaseBuild = build job: 'Release', propagate: true
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
                    toEmail = "shailesh.vaidya@seagate.com"
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