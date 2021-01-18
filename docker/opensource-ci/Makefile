SHELL := /bin/bash
BUILD_ID = 0
RELASE_BUILD = "/var/artifacts/${BUILD_ID}"
RPM_DIR = "/var/artifacts/${BUILD_ID}/cortx_iso"
THIRD_PARTY_VERSION = "third-party-deps-1.0.0-0"

.PHONY: help
## help: print this help message.
help : Makefile
	@echo usage: make \"target\"
	@echo
	@echo Please clone required component repositories in cortx-workspace directory before executing respective targets.
	@echo
	@echo targets:
	@sed -n 's/^##/   /p' $<

## clean: remove existing /var/artifacts/0 directory. 
clean:
	rm -rf "/root/rpmbuild/"
	rm -rf ${RELASE_BUILD}
	mkdir -p ${RPM_DIR}

## build: generate complete CORTX build including third-party-deps at "/var/artifacts/0"
build: io-path control-path release_build

## control-path: generate control-path packages. cortx-provisioner, cortx-monitor, cortx-manager, cortx-management-portal and cortx-ha.
control-path: cortx-prvsnr cortx-monitor cortx-manager cortx-management-portal cortx-ha

## io-path: generate io-path packages. cortx-motr, cortx-s3server and cortx-hare.
io-path: cortx-motr cortx-s3server cortx-hare

## cortx-motr: generate cortx-motr packages.
cortx-motr: _cortx-motr_prereq _cortx-motr_build

## cortx-s3server: generate cortx-s3server packages.
cortx-s3server: cortx-motr _s3_prereq _s3_build

## cortx-hare: generate cortx-hare packages.
cortx-hare: cortx-motr _cortx-hare_prereq _cortx-hare_build

## cortx-ha: generate cortx-ha packages.
cortx-ha: _ha_prereq _ha_build

## cortx-management-portal: generate cortx-management-portal packages.
cortx-management-portal: _cortx-py-utils_build cortx-prvsnr _cortx-management-portal_prereq _cortx-management-portal_build

## cortx-manager: generate cortx-manager packages.
cortx-manager: _cortx-py-utils_build cortx-prvsnr _cortx-manager_prereq _cortx-manager_build

## cortx-monitor: generate cortx-monitor packages.
cortx-monitor: _cortx-py-utils_build _cortx-monitor_prereq _cortx-monitor_build

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
	popd

_cortx-motr_build:
	
	pushd cortx-workspace/cortx-motr && \
		echo "***************  Building cortx-motr RPMS from $$(git rev-parse --short HEAD) *********************" && \
		KERNEL=/lib/modules/$$(yum list installed kernel | tail -n1 | awk '{ print $$2 }').x86_64/build && \
		./autogen.sh || \
		./autogen.sh && \
		./configure --with-linux=$$KERNEL && \
		export build_number=${BUILD_ID} && \
		make rpms && \
		cp /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
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
	popd

_s3_build:
	@echo "***************  Building S3 RPMS *********************"
	
	pushd cortx-workspace/cortx-s3server && \
		yum clean all;rm -rf /var/cache/yum && \
		export build_number=${BUILD_ID} && \
		./rpms/s3/buildrpm.sh -G $$(git rev-parse --short HEAD) && \
		export build_number=${BUILD_ID} && \
	    ./rpms/s3iamcli/buildrpm.sh -G $$(git rev-parse --short HEAD) && \
		cp /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
       	cp /root/rpmbuild/RPMS/noarch/*.rpm ${RPM_DIR} && \
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
		yum localinstall -y ${RPM_DIR}/cortx-motr-[0-9]*.rpm ${RPM_DIR}/cortx-motr-devel-[0-9]*.rpm && \
	popd

_cortx-hare_build:
	@echo "***************  Building cortx-hare RPMS *********************"
	
	pushd cortx-workspace/cortx-hare && \
		echo "Executing build script" && \
		export build_number=${BUILD_ID} && \
		make rpm && \
		cp /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
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
	popd

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
	@echo "***************  Installing cortx-management-portal Prereqsites *********************"
	pushd cortx-workspace/cortx-utils/py-utils && \
		yum install python36-devel -y && \
		python3 setup.py bdist_rpm --post-install utils-post-install --pre-uninstall utils-pre-uninstall --release="${BUILD_ID}_$$(git rev-parse --short HEAD)" && \
		../statsd-utils/jenkins/build.sh -b ${BUILD_ID} && \
		mv /cortx-workspace/cortx-utils/statsd-utils/dist/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
		mv /cortx-workspace/cortx-utils/py-utils/dist/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd

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
		yum localinstall -y ${RPM_DIR}/cortx-py-utils*noarch.rpm ${RPM_DIR}/cortx-prvsnr*.rpm ${RPM_DIR}/python36-cortx-prvsnr*.rpm  && \
        pip3.6 install  pyinstaller==3.5 && \
	popd

_cortx-management-portal_build:
	@echo "***************  Building cortx-management-portal RPMS *********************"
	
	pushd cortx-workspace/cortx-management-portal && \
		BUILD=$$(git rev-parse --short HEAD) && \
		VERSION=$$(cat VERSION) && \
		echo "Executing build script" && \
		echo "VERSION:$$VERSION" && \
		echo "Python:$$(python --version)" && \
		./cicd/build.sh -v $$VERSION -b "${BUILD_ID}" -t -i && \
		cp ./dist/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
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
		yum localinstall -y ${RPM_DIR}/cortx-py-utils*noarch.rpm ${RPM_DIR}/cortx-prvsnr*.rpm ${RPM_DIR}/python36-cortx-prvsnr*.rpm && \
        pip3.6 install  pyinstaller==3.5 && \
	popd

_cortx-manager_build:
	@echo "***************  Building cortx-manager RPMS *********************"
	
	pushd cortx-workspace/cortx-manager && \
		BUILD=$$(git rev-parse --short HEAD) && \
		VERSION=$$(cat VERSION) && \
		echo "Executing build script" && \
		echo "VERSION:$$VERSION" && \
		echo "Python:$(python --version)" && \
		./cicd/build.sh -v $$VERSION -b "${BUILD_ID}" -t -i && \
		cp ./dist/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
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
	popd

_prvsnr_build:
	@echo "***************  Building cortx-prvsnr RPMS *********************"
	
	pushd cortx-workspace/cortx-prvsnr/ && \
		sh ./devops/rpms/buildrpm.sh -g "$$(git rev-parse --short HEAD)" -e 1.0.0 -b "${BUILD_ID}" && \
		sh ./cli/buildrpm.sh -g "$$(git rev-parse --short HEAD)" -e 1.0.0 -b "${BUILD_ID}" && \
		bash ./devops/rpms/api/build_python_api.sh -vv --out-dir /root/rpmbuild/RPMS/x86_64/ --pkg-ver 1.0.0 && \
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
	popd

_cortx-monitor_build:
	@echo "***************  Building sspl RPMS *********************"
	
	pushd cortx-workspace/cortx-monitor && \
		VERSION=$$(cat VERSION) && \
		export build_number=${BUILD_ID} && \
		echo "Executing build script" && \
		echo "VERSION:$$VERSION" && \
		./jenkins/build.sh -l DEBUG && \
		cp /root/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
        cp /root/rpmbuild/RPMS/noarch/*.rpm ${RPM_DIR} && \
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
		yum install cortx-py-utils -y && \
		bash ./jenkins/cicd/cortx-ha-dep.sh  && \
		pip3 install numpy && \
	popd

_ha_build:
	@echo "***************  Building HA RPMS *********************"
	
	pushd "cortx-workspace/cortx-ha" && \
		./jenkins/build.sh -b ${BUILD_ID} && \
		cp dist/rpmbuild/RPMS/x86_64/*.rpm ${RPM_DIR} && \
		createrepo -v ${RPM_DIR} && \
	popd

#***********************************************************************************
#   Component:  DevOps
#	Steps:
#		release_build - Setup yum repo, Generate RELEASE.INFO, gpg key sigining.
#
#***********************************************************************************
release_build:
	@echo "***************  Generating Release Build *********************"

	pushd ${RPM_DIR} && \
		cp /opt/rpm-signing/RPM-GPG-KEY-Seagate . && \
		for rpm in `ls -1 *.rpm`; do expect /opt/rpm-signing/rpm-sign.sh $$rpm; done && \
		createrepo -v . && \
	popd && \
	pushd ${RELASE_BUILD} && \
		sh /opt/release_support/build_release_info.sh ${RPM_DIR} && \
		githubrelease asset seagate/cortx download ${THIRD_PARTY_VERSION} && \
		mkdir -p 3rd_party && tar -xvzf *.tar.gz -C 3rd_party --strip-components=1 && \
	popd

## iso_generation: generate ISO file from release build.
iso_generation:
	@echo "***************  Generating ISO file *********************"
	
	pushd ${RELASE_BUILD} && \
		mkdir -p ${RELASE_BUILD}/iso && \
		genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -publisher Seagate -o ${RELASE_BUILD}/iso/cortx-1.0.0-${BUILD_ID}-single.iso ${RELASE_BUILD} && \
	popd
