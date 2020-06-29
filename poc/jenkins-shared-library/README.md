# [Jenkins Shared Libraries](https://jenkins.io/doc/book/pipeline/shared-libraries/#library-versions)

Jenkins Pipeline shared libraries for CICD deployment.

## Enabled Sandbox

 - Need to [add the shared library](https://jenkins.io/doc/book/pipeline/shared-libraries/#global-shared-libraries) in the Jenkins global configuration. 
 
_Default:_

```groovy
library('jenkins-shared-library')
```

_Specific version:_

```groovy
@Library('jenkins-shared-library@version')_
```

## Disabled Sandbox

_Default:_

```groovy
@Library('http://gitlab.mero.colo.seagate.com/gowthaman.chinnathambi/jenkins-shared-library.git')_
```

_Specific version:_
```groovy
@Library('http://gitlab.mero.colo.seagate.com/gowthaman.chinnathambi/jenkins-shared-library.git@version')_
```
