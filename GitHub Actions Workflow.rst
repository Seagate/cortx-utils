=======================
GitHub Actions Workflow
=======================

GitHub Actions enable you to create custom Software Development Life Cycle (SDLC) workflows directly in your repository. GitHub Actions helps you to automate your software development workflows in the same place you store code, and collaborate on pull requests and issues. Workflows are custom automated processes that you can set up in your repository to build, test, package, release, or deploy any code.

************************
Creating a GitHub Action
************************

To create a GitHub action, perform the procedure mentioned below.

1. At the root of your repository, create a directory named **.github/workflows** to store your workflow files.
2. In **.github/workflows**, add a **.yml** or **.yaml** file for your workflow. For example, **.github/workflows/continuous-integration-workflow.yml**.
3. Refer `Workflow Syntax <https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions>`_ to choose events to trigger an action, add actions, and customize your workflow.
4. Commit your changes in the workflow file to the branch where you want your workflow to run.


For complete information on GitHub actions workflow, refer `GitHub Actions Workflow <https://docs.github.com/en/actions>`_.

Generated Workflows
===================

The links to the generated workflows are mentioned below.

- `https://github.com/Seagate/cortx/blob/master/.github/workflows/update-submodules.yml <https://github.com/Seagate/cortx/blob/master/.github/workflows/update-submodules.yml>`_
- `https://github.com/Seagate/cortx-s3server/blob/dev/.github/workflows/dispatch_submodule_update.yml <https://github.com/Seagate/cortx-s3server/blob/dev/.github/workflows/dispatch_submodule_update.yml>`_

*********
Use Cases
*********
Different use cases associated with the GitHub actions are mentioned below.

- The below mentioned workflow can be used to run python script on push or pull-request events and scheduled time.

 ::
 
  name: Example Workflow
  on: # Mention name of the GitHub event that triggers the workflow or schedule Workflow run
  push: # Trigger the workflow on push
  pull_request: # Trigger the workflow on pull request
  schedule: # # Trigger the workflow on scheduled time
    - cron: '0 0 * * *'  # every day at midnight
  jobs:
   execute-script: # Job-name
    runs-on: ubuntu-latest # Runs job in specified environment
    steps:
    - uses: actions/checkout@v2 # Checkout/Clone repository
    - uses: actions/setup-python@v2 # Action to setup defined python version
      with:
  python-version: '3.x' # Version range or exact version of a Python version to use, using SemVer's version range syntax
        architecture: 'x64' # optional x64 or x86. Defaults to x64 if not specified
    - run: python my_script.py
    
    
- In Cortx, a worflow to generate docker images is displayed below. It is named as **base-docker-image**.
 
  ::
        
   uses: actions/checkout@v2
   name: Set ENV
     run: |
       echo ::set-env name=INPUT_REPOSITORY::$( echo $GITHUB_REPOSITORY | tr '[:upper:]' '[:lower:]')
       echo ::set-env name=IMAGE_NAME::cortx_centos
       echo ::set-env name=TAG::7.7.1908
   - name: Build and push Docker images
     uses: docker/build-push-action@v1.1.0
     env:
         DEFAULT_PASSWORD: ${{ secrets.DEFAULT_PASSWORD }}
         REPO_NAME: ${{ github.event.repository.name }}
     with:
       # Path to the Dockerfile (Default is '{path}/Dockerfile')
       dockerfile: docker/cortx_components/centos/Dockerfile 
       # Build Arguments for docker image build. 
       build_args: 'CENTOS_RELEASE=7.7.1908,USER_PASS=root:"$DEFAULT_PASSWORD"'
       path: docker/cortx_components/centos/
       username: ${{ github.actor }}
       password: ${{ secrets.GITHUB_TOKEN }}
       registry: docker.pkg.github.com
       repository: ${{ env.INPUT_REPOSITORY }}/${{ env.IMAGE_NAME }}
       tags: ${{ env.TAG }}
       
- In Cortx, a workflow to generate component rpm is mentioned below. In this case, it is for Provisioner.
  
   ::
   
    jobs:
  # This workflow contains a single job called "build"
  build:
    # The type of runner that the job will run on
    runs-on: ubuntu-latest

    # Steps represent a sequence of tasks that will be executed as part of the job
    steps:
    # Checks-out your repository under $GITHUB_WORKSPACE, so your job can access it
    - uses: actions/checkout@v2
    
    - name: Checkout
      uses: actions/checkout@v2
      with:
        # Repository name with owner. For example, actions/checkout
        repository: Seagate/cortx-prvsnr
        token: ${{ secrets.TOKEN }}
        path: provisioner

    # Runs a set of commands using the runners shell
    - name: Build Provisioner packages
      run: |
        echo "${{ secrets.GITHUB_TOKEN }}" | docker login docker.pkg.github.com -u ${{ github.actor }} --password-stdin
        docker pull docker.pkg.github.com/seagate/cortx-re/cortx_centos:7.7.1908
        docker run -i -v $PWD:/build docker.pkg.github.com/seagate/cortx-re/cortx_centos:7.7.1908 'sh /build/build_scripts/build_provisoiner.sh'
       
    - name: Upload files to a GitHub release
      uses: svenstaro/upload-release-action@2.0.0
      with:
        repo_token: ${{ secrets.TOKEN }}
        release_name: provisioner
        file: provisioner/release/*.rpm
        tag: 1.0.0
        file_glob: true
        body: "Provisioner Release"

