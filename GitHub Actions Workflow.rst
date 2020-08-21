=======================
GitHub Actions Workflow
=======================

GitHub Actions enable you to create custom software development life cycle (SDLC) workflows directly in your repository. GitHub Actions helps you to automate your software development workflows in the same place you store code, and collaborate on pull requests and issues. Workflows are custom automated processes that you can set up in your repository to build, test, package, release, or deploy any code.

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
