import re
import git
import yaml
import shutil
import logging
import requests
import argparse
import tempfile
from github import Github
from datetime import datetime

class AutoMerge:
    
    # Github orgranization 
    github_org      = "###ORG_NAME###"
    
    # Dynamic component map that holds all information on this auto merge workflow.
    component_map   = {
        "cortx-s3server"    : { 'repo_url' : "https://github.com/{}/cortx-s3server.git".format(github_org),         'repo_name' : 'cortx-s3server'},
        "cortx-motr"        : { 'repo_url' : "https://github.com/{}/cortx-motr.git".format(github_org),             'repo_name' : 'cortx-motr'},
        "cortx-hare"        : { 'repo_url' : "https://github.com/{}/cortx-hare.git".format(github_org),             'repo_name' : 'cortx-hare'},
        "cortx-ha"          : { 'repo_url' : "https://github.com/{}/cortx-ha.git".format(github_org),               'repo_name' : 'cortx-ha'},
        "cortx-prvsnr"      : { 'repo_url' : "https://github.com/{}/cortx-prvsnr.git".format(github_org),           'repo_name' : 'cortx-prvsnr'},
        "cortx-sspl"        : { 'repo_url' : "https://github.com/{}/cortx-monitor.git".format(github_org),          'repo_name' : 'cortx-monitor'},
        "cortx-csm_agent"   : { 'repo_url' : "https://github.com/{}/cortx-manager.git".format(github_org),          'repo_name' : 'cortx-manager'},
        "cortx-csm_web"     : { 'repo_url' : "https://github.com/{}/cortx-management-portal.git".format(github_org),'repo_name' : 'cortx-management-portal'},
        "cortx-py-utils"    : { 'repo_url' : "https://github.com/{}/cortx-utils.git".format(github_org),            'repo_name' : 'cortx-utils'},
    } 
    
    '''
    This method initialize all the required attributes for this auto merge workflow
    and make it available through out the class.
    '''
    def __init__(self, release_info_url, target_branch, github_token, logger):
        
        self.logger             = logger
        
        self.logger.info("Entering __init__ method......")

        self.release_info_url   = release_info_url
        self.temp_dir           = tempfile.mkdtemp()
        self.github             = Github(github_token)
        self.target_branch      = target_branch
        

        self.logger.info("""
                Provided Parameters : 
                    Release Info URL = {} 
                    Target Branch    = {}
                    Temp Branch      = {}""".format(self.release_info_url,self.target_branch,self.temp_dir))
        self.logger.info("Exiting ......\n")

    '''
    Read build informations like release/component build number, component commit hash
    from the provided RELEASE.INFO file and push it to common config map for further
    execution.  
    '''
    def get_build_info(self):
        self.logger.info("Entering ......")
        
        release_info    = yaml.safe_load(requests.get(self.release_info_url).content)
        components_rpm  = release_info['COMPONENTS']
        source_branch   = release_info['BRANCH']
        release_build   = release_info['BUILD']

        for rpm in components_rpm:
            matchObj = re.match( r'([a-z0-9_-]+)-([0-9]+.[0-9]+.[0-9]+)-([0-9]+)_([a-z0-9]+)', rpm, re.M|re.I) 
            if matchObj and matchObj.group(1) in self.component_map:
                component_name      = matchObj.group(1)
                commit_hash         = (matchObj.group(4).replace("git",""))[:7]
                component_build     = matchObj.group(3)
                component_info_map  = self.component_map[component_name]
                
                component_info_map.update({"commit" : commit_hash, 'source_branch':source_branch, 'release_build':release_build, 'component_build':component_build})
                self.component_map.update({ component_name : component_info_map})
        
                self.logger.info("""{} : Build Commit = {}, Source Branch = {}, Release Build = {}, Component Build = {}""".format(component_name, commit_hash, source_branch, release_build, component_build))
        self.logger.info("Exiting ......\n")
    
    '''
    Clone all component git repo locally to validate the commit exists on the target branch
    and create merge branch for the applicabel components.
    '''
    def clone_git_repo(self):
        self.logger.info("Entering ......")

        for component in self.component_map:
        
            repo_path   = "{}/{}".format(self.temp_dir,component)
            repo        = git.Repo.clone_from(self.component_map[component]['repo_url'], repo_path, branch=self.component_map[component]['source_branch'])

            self.logger.info("{}".format(repo))
            
            component_info_map = self.component_map[component] 
            component_info_map.update({ 'repo_path' : repo_path, 'repo_obj': repo})
            self.component_map.update({component : component_info_map})
            
        self.logger.info("Exiting ......\n")

    
    '''
    Validate the provided build commit exists on the target branch and save the info in 
    common component map.
    '''
    def get_component_status(self):
        self.logger.info("Entering ......")
        
        for component in self.component_map:
            repo_object = self.component_map[component]['repo_obj']
            try:
                result=repo_object.git.branch('-a','--contains', self.component_map[component]['commit'])

                self.logger.debug("commit contains branch = {}".format(result))
                
                if self.target_branch in result:
                    contains_commit = True
                else:
                    contains_commit = False
            except:
                contains_commit = False
            
            self.logger.info("{} : {} branch contains commit '{}' ? {}".format(component, self.target_branch,self.component_map[component]['commit'], contains_commit))
            
            component_info_map = self.component_map[component]
            component_info_map.update({ 'target_contains_commit' : contains_commit })
            self.component_map.update({component : component_info_map})

        self.logger.info("Exiting ......\n")

    
    '''
    Create merge branch and PR for the applicable components.
    '''
    def create_git_pr(self):
        self.logger.info("Entering ......")

        for component in self.component_map:

            if (not self.component_map[component]['target_contains_commit'])  and 'repo_obj' in self.component_map[component] and 'commit' in self.component_map[component]:

                repo_object     = self.component_map[component]['repo_obj']
                commit          = self.component_map[component]['commit']
                component_build = self.component_map[component]['component_build']
                release_build   = self.component_map[component]['release_build']
                today_date      = datetime.today().strftime('%Y%m%d')
                merge_branch    = "{}_{}_{}".format(release_build,component_build,today_date)

                self.logger.info("{} : Build Commit = {}, Merge branch = {}, Target Branch = {}".format(component, commit, merge_branch, self.target_branch))

                self.create_git_branch(component, repo_object, commit, merge_branch)

                repo    = self.github.get_repo("{}/{}".format(self.github_org,self.component_map[component]['repo_name']))

                title   = "[ Automated Merge ] : Release Build {} is ready for {} merge".format(release_build, self.target_branch)
                body    = "RELEASE.INFO => \n {}".format(self.release_info_url)

                pulls_count = 0
                pulls = repo.get_pulls(state='open', head=merge_branch, base=self.target_branch)
                for pull in pulls:
                    pulls_count += 1
                if pulls_count > 0 :
                    self.logger.info("{} : Pull request already exsits...skipping pr creation = {}".format(component, pulls[0]))
                    pr = pulls[0]
                else:
                    pr = repo.create_pull(title=title, body=body, head=merge_branch, base=self.target_branch)
                    self.logger.info("{} : Pull request created {}".format(component,pr))

                    pulls = repo.get_pulls(state='open', head=merge_branch, base=self.target_branch)
                    for pull in pulls:
                        pr = pull

                component_info_map = self.component_map[component]
                component_info_map.update({ 'pr' : pr })
                self.component_map.update({component : component_info_map})

            else:
                self.logger.info("{}: Target branch '{}' already contains commit '{}' skipping PR workflow....".format(component, self.target_branch, self.component_map[component]['commit']))

        self.logger.info("Exiting ......\n")

    '''
    Create merge branch for the applicable components.
    '''
    def create_git_branch(self, component, repo_object, commit, branch_name):
        merge_branch = repo_object.create_head(branch_name, commit) 
        merge_branch.checkout()
        repo_object.git.push('--set-upstream', 'origin', merge_branch)
        self.logger.info(" {} : Pushed merge branch '{}' to remote".format(component, merge_branch))

    '''
    Merge the created component PR.
    '''
    def merge_pr(self):

        self.logger.info("Entering ......")
        for component in self.component_map:

            if 'pr' in self.component_map[component]: 
                
                pr = self.component_map[component]['pr']
                
                if pr.mergeable:
                    result = pr.merge()
                    self.logger.info("{} : Merged the PR = {}".format(component, result))
                else:
                    self.logger.error("{} : PR is not mergeable, state = {}".format(component, pr.mergeable_state))
            
            else:
                self.logger.info("{} : PR not created for the component skipping merge...".format(component))
        self.logger.info("Exiting ......\n")

    '''
    Cleanup the local temp workspace on post execution.
    '''
    def cleanup(self):
        self.logger.info("Entering ......")
        shutil.rmtree(self.temp_dir)
        self.logger.info("Temp Directory removed : {}".format(self.temp_dir))
        self.logger.info("Exiting ......\n")  


############################################ INPUT ARGUMENTS ################################################################

parser = argparse.ArgumentParser(description='Auto Merge input parameters.')
parser.add_argument('-r', '--release_info', help='Cortx Build RELEASE.INFO file absolute path', required=True)
parser.add_argument('-t', '--target_branch', help='Target branch name (the build commit merged to this branch)', required=True)
parser.add_argument('-x', '--github_token', help='Github credentials to authenticate', required=True)
parser.add_argument('-l', '--log_level', default='INFO',help='set log level')

args = parser.parse_args()

# Logger Initilization
logging.basicConfig(format="[ %(funcName)s ] : %(message)s", level=args.log_level)
logger = logging.getLogger('root')

# 00. Initialize Automerge Class with all input parameters (release info file location, target merge branch and github access token).
obj = AutoMerge(args.release_info, args.target_branch, args.github_token, logger)

try:
    # 01. Retrive build information from the RELEASE.INO yaml file.
    obj.get_build_info()

    # 02. Clone all component github repositories locally.
    obj.clone_git_repo()

    # 03. Get component commit status 
    obj.get_component_status()

    # 04. Create PR and merge the changes for the applicable components (if commit exsits in target branch then we can skip merge)
    obj.create_git_pr()

    # 05. Merge PR
    obj.merge_pr()

finally:
    # Perform cleanup on post execution
    obj.cleanup()
