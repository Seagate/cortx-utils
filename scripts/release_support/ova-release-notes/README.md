# Automated pre-release with release notes generation for OVA

## Description
Create a OVA pre-release in [`Seagate/cortx`](https://github.com/Seagate/cortx) repository with release-notes includes features, bugfixes and general changes happened since last release.

## How to create OVA pre-release with release-notes
1. Install all dependencies mentioned in `requirements.txt`.

2. Run `ova_release.py` script with required arguments as follow
  
```
python3 ova_release.py -u <JIRA Username> -p <JIRA Password> --build <OVA Build Number> --release <GitHub Release Number> --sourceBuild <CORTX Build    Number> --targetBuild <CORTX Build Number>
```
  
  Parameters:
    
    -u : JIRA Username
    
    -p : JIRA Password
    
    --build : OVA Build number (Internally pre-fix build number with `cortx-ova-build` e.g. `cortx-ova-build-<Build Number>`)
    
    --release : GitHub pre-release version number
    
    --sourceBuild : CORTX build number used to build previous OVA release
    
    --targetBuild : CORTX build number used to build current OVA release
