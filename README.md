[![Codacy Badge](https://app.codacy.com/project/badge/Grade/edb2670e6aa24aeb899c496c15b596c9)](https://www.codacy.com?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Seagate/cortx-re&amp;utm_campaign=Badge_Grade) [![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://github.com/Seagate/cortx-re/blob/main/LICENSE)

# Cortx Release Engineering
The purpose of this repository is to keep the scripts, tools, and other configuration used in the Release Engineering. 

Release Engineering team is responsible for the followings

-   Cortx Project CI Build Process.
-   Managing cortx-storage for artifact hosting.
-   Automation to support cortx project.

## Repo Structure

An overview of folder structure in cortx-rerepo
```console
├───docker
├───jenkins
└───scripts
```
### Docker
-   We have containerized Release engineering infrastructure to eliminate host and OS dependency. The dockerfiles, docker-compose files used to build this containers are available under this folder.

### Jenkins ( Experimental usage )
-   Jenkins job configurations, groovy scripts and template used in the Jenkins are available under this folder.

### Scripts
-   Shell, python scripts used in the RE process automation are available under this folder.
-   Scripts like changelog generation, build manifest generation, rpm validation..etc  are available under this folder

## Support
The below table explains  RE support process.

| Type                      |  Priority     | ETA                                                       |
|---------------------------|---------------|-----------------------------------------------------------|
| New Requirement           | Major/Minor   | Groomed -> Planed -> Implemented in next immediate sprint |
| Bug                       | Minor         | Addressed in next immediate sprint                        |
| Bug                       | Major         | Addressed ASAP                                            |
| KT/Clarification/Demo     | minor         | Based on RE Engineer availability                         |

It's recommended to create Jira tickets for all the above process by that way discussions are tracked and responded ASAP.

_Note : Add **RE** as component while raising Jira ticket_ (e.g. https://jts.seagate.com/browse/EOS-11732 )

## Documents 

All RE related documents are available in the below locations
-   [RE GitHub Wiki](https://github.com/Seagate/cortx-re/wiki)
-   [Cortx Dev SharePoint](https://seagatetechnology.sharepoint.com/:f:/r/sites/gteamdrv1/tdrive1224/Shared%20Documents/Components/Release%20Engineering/Documentation?csf=1&web=1&e=LdXiz4)
