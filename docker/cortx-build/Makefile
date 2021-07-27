SHELL := /bin/bash
BUILD_ID = 0
RELEASE_VERSION = "2.0.0"
RELEASE_BUILD = "/var/artifacts/${BUILD_ID}"
RPM_DIR = "/var/artifacts/${BUILD_ID}/cortx_iso"
THIRD_PARTY_VERSION = "1.0.0-0"
BRANCH = "main"

.PHONY: help
## help: print this help message.
help : Makefile
	@echo usage: make \"target\"
	@echo
	@echo Please clone required component repositories in cortx-workspace directory before executing respective targets.
	@echo
	@echo targets:
	@sed -n 's/^##/   /p' $<
	
## checkout: checkout specified branch/tag code
checkout:
	@echo "*************** checkout code *********************"
	pushd cortx-workspace && \
		for component in $$(ls -1d cortx-* | grep -Evx 'cortx-experiments||cortx-posix||cortx-multisite'); do pushd $$component; git pull -p --all; git checkout $$BRANCH || exit 1; popd ; done  && \
	popd || (echo "ERROR: Failed to checkout specified branch/tag Exiting..."; exit 1)

## clean: remove existing /var/artifacts/0 directory. 
clean:
	rm -rf "/root/rpmbuild/"
	rm -rf ${RELEASE_BUILD}
	mkdir -p ${RPM_DIR}

## build: generate complete CORTX build including third-party-deps at "/var/artifacts/0"
build: io-path control-path cortx-prereq release_build

## control-path: generate control-path packages. cortx-provisioner, cortx-monitor, cortx-manager, cortx-management-portal and cortx-ha.
control-path: cortx-prvsnr cortx-monitor cortx-manager cortx-management-portal cortx-ha

## io-path: generate io-path packages. cortx-motr, cortx-s3server and cortx-hare.
io-path: cortx-motr cortx-s3server cortx-hare

## cortx-motr: generate cortx-motr packages.
cortx-motr: _cortx-motr_prereq _cortx-motr_build

## cortx-s3server: generate cortx-s3server packages.
cortx-s3server: cortx-motr _s3_prereq _s3_build

## cortx-hare: generate cortx-hare packages.
cortx-hare: cortx-motr _cortx-py-utils_build _cortx-py-utils_install _cortx-hare_prereq _cortx-hare_build

## cortx-ha: generate cortx-ha packages.
cortx-ha: _cortx-py-utils_build _cortx-py-utils_install _ha_prereq _ha_build

## cortx-management-portal: generate cortx-management-portal packages.
cortx-management-portal: _cortx-py-utils_build _cortx-py-utils_install cortx-prvsnr _cortx-management-portal_prereq _cortx-management-portal_build

## cortx-manager: generate cortx-manager packages.
cortx-manager: _cortx-py-utils_build _cortx-py-utils_install cortx-prvsnr _cortx-manager_prereq _cortx-manager_build

## cortx-monitor: generate cortx-monitor packages.
cortx-monitor: _cortx-py-utils_build _cortx-py-utils_install _cortx-monitor_prereq _cortx-monitor_build

## cortx-posix: generate cortx-posix (NFS) packages.
cortx-posix: _cortx-posix_prereq _cortx-posix_build

## cortx-prvsnr: generate cortx-prvsnr packages.
cortx-prvsnr: _prvsnr_prereq _prvsnr_build

#***********************************************************************************
#   Component:  cortx-motr
#	Steps:
#		_cortx-motr_prereq - Install Prerequisites to Generate cortx-motr RPM	
#		_cortx-motr_build  - Script to Generate cortx-motr RPM
#
#***********************************************************************************
_cortx-motr_prereq:
	@echo "***************  Installing cortx-motr Prereqsites *********************"

	pushd cortx-workspace/cortx-motr && \
		export build_number=${BUILD_ID} && \
		kernel_src=$$(ls -1rd /lib/modules/*/build | head -n1) && \
		cp cortx-motr.spec.in cortx-motr.spec && \
		sed -i 's/@.*@/111/g' cortx-motr.spec && \
		yum-builddep -y cortx-motr.spec && \
	popd || (echo "ERROR: cortx-motr source code is not available in cortx-workspace. Exiting..."; exit 1)

_cortx-motr_build:
	
	pushd cortx-workspace/cortx-motr && \
		echo "***************  Building cortx-motr RPMS from $$(git rev-parse --short HEAD) *********************" && \
		KERNEL=/lib/modules/$$(yum list installed kernel | tail -n1 | awk '{ print $$2 }').x86_64/build && \
		./autogen.sh || \
		./autogen.sh && \
		./configure --with-linux=$$KERNEL && \
		export build_number=${BUILD_ID} && \
		make rpms && \
		rm -rf ${RPM_DIR}/cortx-motr*.rpm && \
		mv /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd

#***********************************************************************************
#   Component:  S3
#	Steps:
#		_s3_prereq - Install Prerequisites to Generate S3 RPM	
#		_s3_build  - Script to Generate S3 RPM
#
#***********************************************************************************
_s3_prereq:
	@echo "***************  Installing S3 Prereqsites *********************"

	pushd cortx-workspace/cortx-s3server && \
	  yum localinstall -y ${RPM_DIR}/cortx-motr-[0-9]*.rpm ${RPM_DIR}/cortx-motr-devel-[0-9]*.rpm && \
		yum clean all;rm -rf /var/cache/yum && \
	popd || (echo "ERROR: cortx-s3server source code is not available in cortx-workspace. Exiting..."; exit 1)

_s3_build:
	@echo "***************  Building S3 RPMS *********************"
	
	pushd cortx-workspace/cortx-s3server && \
		yum clean all;rm -rf /var/cache/yum && \
		export build_number=${BUILD_ID} && \
		./rpms/s3/buildrpm.sh -S ${RELEASE_VERSION} -G $$(git rev-parse --short HEAD) && \
		./rpms/s3iamcli/buildrpm.sh -S ${RELEASE_VERSION} -G $$(git rev-parse --short HEAD) && \
		./rpms/s3test/buildrpm.sh -S ${RELEASE_VERSION} -G $$(git rev-parse --short HEAD) && \
		rm -rf {RPM_DIR}/cortx-s3*.rpm && \
		mv /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
       	mv /root/rpmbuild/RPMS/noarch/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd

#***********************************************************************************
#   Component:  cortx-hare
#	Steps:
#		_cortx-hare_prereq - Install Prerequisites to Generate cortx-hare RPM	
#		_cortx-hare_build  - Script to Generate cortx-hare RPM
#
#***********************************************************************************
_cortx-hare_prereq:
	@echo "***************  Installing cortx-hare Prereqsites *********************"

	pushd cortx-workspace/cortx-hare && \
		yum localinstall -y ${RPM_DIR}/cortx-py-utils*noarch.rpm ${RPM_DIR}/cortx-motr-[0-9]*.rpm ${RPM_DIR}/cortx-motr-devel-[0-9]*.rpm && \
	popd || (echo "ERROR: cortx-hare source code is not available in cortx-workspace. Exiting..."; exit 1)

_cortx-hare_build:
	@echo "***************  Building cortx-hare RPMS *********************"
	
	pushd cortx-workspace/cortx-hare && \
		echo "Executing build script" && \
		export build_number=${BUILD_ID} && \
		make VERSION=${RELEASE_VERSION} rpm && \
		rm -rf ${RPM_DIR}/cortx-hare*.rpm && \
		mv /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd


#***********************************************************************************
#   Component:  cortx-posix
#	Steps:
#		_cortx-posix_prereq - Install Prerequisites to Generate cortx-posix RPM	
#		_cortx-posix_build  - Script to Generate cortx-posix RPM
#
#***********************************************************************************
_cortx-posix_prereq:
	@echo "***************  Installing cortx-posix Prereqsites *********************"

	pushd cortx-workspace/cortx-posix && \
		yum localinstall -y ${RPM_DIR}/cortx-motr-[0-9]*.rpm ${RPM_DIR}/cortx-motr-devel-[0-9]*.rpm && \
		yum install libevhtp libevhtp-devel libevent libevent-devel userspace-rcu-devel dbus-devel -y && \
		sed -i 's/QA_CHECK_RPATHS=1/QA_CHECK_RPATHS=0/g' ~/.rpmmacros && \
	popd || (echo "ERROR: cortx-posix source code is not available in cortx-workspace. Exiting..."; exit 1)

_cortx-posix_build:
	@echo "***************  Building cortx-posix RPMS *********************"
	git clone https://github.com/Seagate/nfs-ganesha --recursive --branch 2.8-stable-cortx
	pushd cortx-workspace/cortx-posix && \
			VERSION=$$(cat VERSION) && \
			echo "Executing build script" && \
			echo "VERSION:$$VERSION" && \
			./jenkins/build.sh -v $$VERSION -b ${BUILD_ID} -p ../../nfs-ganesha/src/  && \
			cp /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
			createrepo -v ${RPM_DIR} && \
	popd
	

#***********************************************************************************
#   Component:  cortx-py-utils
#       Steps:
#               _cortx-py-utils_build  - Script to Generate cortx-py-utils RPM
#
#***********************************************************************************

_cortx-py-utils_build:
	@echo "***************  Building cortx-py-utils package *********************"
	pushd cortx-workspace/cortx-utils/ && \
		yum install python36-devel -y && \
		./jenkins/build.sh -v ${RELEASE_VERSION} -b ${BUILD_ID} && \
		./statsd-utils/jenkins/build.sh -b ${BUILD_ID} && \
		rm -rf ${RPM_DIR}/cortx-py-utils*.rpm && \
		mv /cortx-workspace/cortx-utils/statsd-utils/dist/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
		mv /cortx-workspace/cortx-utils/py-utils/dist/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd || (echo "ERROR: cortx-utils source code is not available in cortx-workspace. Exiting..."; exit 1)

_cortx-py-utils_install:
	@echo "***************  Installing cortx-py-utils package *********************"
	pushd cortx-workspace/cortx-utils/py-utils && \
		yum install python3-pip gcc python3-devel -y && \
		yum erase python36-PyYAML -y && \
		pip3 install -r python_requirements.txt && \
		pip3 install -r python_requirements.ext.txt && \
		yum localinstall -y ${RPM_DIR}/cortx-py-utils*noarch.rpm && \
	popd || (echo "ERROR: Failed to install cortx-utils package. Exiting..."; exit 1) 	

#***********************************************************************************
#   Component:  cortx-management-portal
#	Steps:
#		_cortx-management-portal_prereq - Install Prerequisites to Generate cortx-management-portal RPM	
#		_cortx-management-portal_build  - Script to Generate cortx-management-portal RPM
#
#***********************************************************************************
_cortx-management-portal_prereq:
	@echo "***************  Installing cortx-management-portal Prereqsites *********************"
	pushd cortx-workspace/cortx-management-portal && \
		yum localinstall ${RPM_DIR}/cortx-prvsnr*.rpm ${RPM_DIR}/python36-cortx-prvsnr*.rpm  && \
        pip3.6 install pyinstaller==3.5 && \
	popd || (echo "ERROR: cortx-management-portal source code is not available in cortx-workspace. Exiting..."; exit 1)

_cortx-management-portal_build:
	@echo "***************  Building cortx-management-portal RPMS *********************"
	
	pushd cortx-workspace/cortx-management-portal && \
		BUILD=$$(git rev-parse --short HEAD) && \
		echo "Python:$$(python --version)" && \
		./cicd/build.sh -v ${RELEASE_VERSION} -v ${RELEASE_VERSION} -b "${BUILD_ID}" -t -i && \
		rm -rf ${RPM_DIR}/cortx-csm_web*.rpm && \
		mv ./dist/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd


#***********************************************************************************
#   Component:  cortx-manager
#	Steps:
#		_cortx-manager_prereq - Install Prerequisites to Generate cortx-manager RPM	
#		_cortx-manager_build  - Script to Generate cortx-manager RPM
#
#***********************************************************************************
_cortx-manager_prereq:
	@echo "***************  Installing cortx-manager Prereqsites *********************"

	pushd cortx-workspace/cortx-manager && \
		yum localinstall -y ${RPM_DIR}/cortx-prvsnr*.rpm ${RPM_DIR}/python36-cortx-prvsnr*.rpm && \
        pip3.6 install pyinstaller==3.5 && \
	popd || (echo "ERROR: cortx-manager source code is not available in cortx-workspace. Exiting..."; exit 1)

_cortx-manager_build:
	@echo "***************  Building cortx-manager RPMS *********************"
	
	pushd cortx-workspace/cortx-manager && \
		BUILD=$$(git rev-parse --short HEAD) && \
		echo "Python:$(python --version)" && \
		./cicd/build.sh -v ${RELEASE_VERSION} -b "${BUILD_ID}" -t -i || \
		rm -rf ${RPM_DIR}/cortx-csm_agent*.rpm && \
		mv ./dist/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd

#***********************************************************************************
#   Component:  cortx-prvsnr
#	Steps:
#		_prvsnr_prereq - Install Prerequisites to Generate cortx-prvsnr RPM	
#		_prvsnr_build  - Script to Generate cortx-prvsnr RPM
#
#***********************************************************************************
_prvsnr_prereq:
	@echo "***************  Installing cortx-prvsnr Prereqsites *********************"

	pushd cortx-workspace/cortx-prvsnr/ && \
		yum install -y python && \
	popd || (echo "ERROR: cortx-prvsnr codebase is not available in cortx-workspace.Exiting..."; exit 1)

_prvsnr_build:
	@echo "***************  Building cortx-prvsnr RPMS *********************"
	
	pushd cortx-workspace/cortx-prvsnr/ && \
        rm -rf ${RPM_DIR}/*cortx-prvsnr*.rpm /root/rpmbuild/RPMS/x86_64/*cortx-prvsnr*.rpm && \
		sh ./devops/rpms/buildrpm.sh -g "$$(git rev-parse --short HEAD)" -e ${RELEASE_VERSION} -b "${BUILD_ID}" && \
		sh ./cli/buildrpm.sh -g "$$(git rev-parse --short HEAD)" -e ${RELEASE_VERSION} -b "${BUILD_ID}" && \
		bash ./devops/rpms/api/build_python_api.sh -vv --out-dir /root/rpmbuild/RPMS/x86_64/ --pkg-ver ${BUILD_ID}_git$$(git rev-parse --short HEAD) && \
        if [ -f ./devops/rpms/lr-cli/build_python_cortx_setup.sh ]; then bash ./devops/rpms/lr-cli/build_python_cortx_setup.sh -vv --out-dir /root/rpmbuild/RPMS/x86_64/ --pkg-ver ${BUILD_ID}_git$$(git rev-parse --short HEAD); fi && \
        cp /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd

#***********************************************************************************
#   Component:  sspl
#	Steps:
#		_sspl_prereq - Install Prerequisites to Generate sspl RPM	
#		_sspl_build  - Script to Generate sspl RPM
#
#***********************************************************************************
_cortx-monitor_prereq:
	@echo "***************  Installing sspl Prereqsites *********************"

	pushd cortx-workspace/cortx-monitor && \
		yum localinstall -y ${RPM_DIR}/cortx-py-utils*noarch.rpm && \
		yum install sudo python-Levenshtein libtool doxygen python-pep8 openssl-devel graphviz check-devel -y && \
	popd || (echo "ERROR: cortx-monitor source code is not available in cortx-workspace. Exiting..."; exit 1)

_cortx-monitor_build:
	@echo "***************  Building sspl RPMS *********************"
	
	pushd cortx-workspace/cortx-monitor && \
		export build_number=${BUILD_ID} && \
		echo "Executing build script" && \
		./jenkins/build.sh -v ${RELEASE_VERSION} -l DEBUG && \
		rm -rf ${RPM_DIR}/*sspl*.rpm && \
		mv /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
        mv /root/rpmbuild/RPMS/noarch/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd

#***********************************************************************************
#   Component:  HA
#	Steps:
#		_ha_prereq - Install Prerequisites to Generate HA RPM	
#		_ha_build  - Script to Generate HA RPM
#
#***********************************************************************************
_ha_prereq:
	@echo "***************  Installing HA Prereqsites *********************"
	
	pushd "cortx-workspace/cortx-ha" && \
		yum clean all;rm -rf /var/cache/yum && \
		yum erase python36-PyYAML -y && \
		bash ./jenkins/cicd/cortx-ha-dep.sh  && \
		pip3 install numpy && \
	popd || (echo "ERROR: cortx-ha source code is not available in cortx-workspace. Exiting..."; exit 1)

_ha_build:
	@echo "***************  Building HA RPMS *********************"
	
	pushd "cortx-workspace/cortx-ha" && \
		./jenkins/build.sh -v ${RELEASE_VERSION} -b ${BUILD_ID} && \
		rm -rf ${RPM_DIR}/cortx-ha-*.rpm && \
		mv dist/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd

#***********************************************************************************
#   Component:  DevOps
#	Steps:
#		release_build - Setup yum repo, Generate RELEASE.INFO, gpg key sigining.
#
#***********************************************************************************
cortx-prereq:
	@echo "***************  Generating cortx-prereq RPM *********************"

	pushd /opt/third-party-rpm/ && \
		./build-prerequisite-rpm.sh -v ${RELEASE_VERSION} -r ${BUILD_ID} -g $$GIT_HASH && \
		rm -rf ${RPM_DIR}/cortx-prereq*.rpm && \
		mv /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
	popd

release_build:
	@echo "***************  Generating Release Build *********************"

	pushd ${RPM_DIR} && \
		cp /opt/rpm-signing/RPM-GPG-KEY-Seagate . && \
		for rpm in `ls -1 *.rpm`; do expect /opt/rpm-signing/rpm-sign.sh $$rpm; done && \
		createrepo -v . && \
	popd && \
	pushd ${RELEASE_BUILD} && \
		githubrelease asset seagate/cortx download third-party-deps-${THIRD_PARTY_VERSION} && \
		mkdir -p 3rd_party && tar -xvzf third-party-centos-7.8.2003-${THIRD_PARTY_VERSION}.tar.gz -C 3rd_party --strip-components=1 && \
		mkdir -p python_deps && tar -xvzf python-deps-${THIRD_PARTY_VERSION}.tar.gz -C python_deps --strip-components=1 && \
		cortx_prvsnr_preq=$$(ls /var/artifacts/0/cortx_iso/python36-cortx-prvsnr* | awk -F'_' '{split($$(NF-1), A ,"."); gsub("git", "", A[1]); print A[1]}') && \
		wget -O install-${RELEASE_VERSION}-${BUILD_ID}.sh https://raw.githubusercontent.com/Seagate/cortx-prvsnr/$$cortx_prvsnr_preq/srv/components/provisioner/scripts/install.sh && \
 		sh /opt/release_support/build_release_info.sh -b ${BRANCH} -v ${RELEASE_VERSION} -l ${RPM_DIR} -t ${RELEASE_BUILD}/3rd_party && \
	popd

## iso_generation: generate ISO file from release build.
iso_generation:
	@echo "***************  Generating ISO file *********************"
	
	pushd ${RELEASE_BUILD} && \
		mkdir -p ${RELEASE_BUILD}/iso && \
		genisoimage -input-charset iso8859-1 -exclude "python-deps-${THIRD_PARTY_VERSION}.tar.gz" -m "third-party-centos-7.8.2003-${THIRD_PARTY_VERSION}.tar.gz" -f -J -joliet-long -r -allow-lowercase -allow-multidot -publisher Seagate -o ${RELEASE_BUILD}/iso/cortx-1.0.0-${BUILD_ID}-single.iso ${RELEASE_BUILD} && \
	popd