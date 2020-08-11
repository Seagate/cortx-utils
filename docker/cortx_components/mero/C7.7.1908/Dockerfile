# Builder image

ARG  CENTOS_RELEASE
FROM ssc-vm-0279.colo.seagate.com:5000/centos_eos:${CENTOS_RELEASE} as lustre-rpm-builder

ARG LUSTRE_VERSION

COPY lustre-2.9.0.spec.patch .
ADD  https://downloads.whamcloud.com/public/lustre/lustre-${LUSTRE_VERSION}/el7/client/SRPMS/lustre-${LUSTRE_VERSION}-1.src.rpm .

RUN rpm -i lustre-${LUSTRE_VERSION}-1.src.rpm
RUN patch -p1 -i lustre-2.9.0.spec.patch /root/rpmbuild/SPECS/lustre.spec
RUN yum -y install kernel gcc make kernel-devel
RUN yum-builddep -y /root/rpmbuild/SPECS/lustre.spec
RUN QA_RPATHS=255 rpmbuild -bb --without servers --without lustre-tests \
        --define 'configure_args --disable-gss-keyring' \
        --define "kver `ls -1r /lib/modules | head -n1`" \
        /root//rpmbuild/SPECS/lustre.spec

# Final image

ARG  CENTOS_RELEASE
FROM ssc-vm-0279.colo.seagate.com:5000/centos_eos:${CENTOS_RELEASE}

ARG LUSTRE_VERSION

COPY --from=lustre-rpm-builder /root/rpmbuild/RPMS/x86_64/lustre-client-devel-${LUSTRE_VERSION}*.rpm .

RUN wget https://downloads.whamcloud.com/public/lustre/lustre-${LUSTRE_VERSION}/el7/client/RPMS/x86_64/kmod-lustre-client-${LUSTRE_VERSION}-1.el7.x86_64.rpm \
         https://downloads.whamcloud.com/public/lustre/lustre-${LUSTRE_VERSION}/el7/client/RPMS/x86_64/lustre-client-${LUSTRE_VERSION}-1.el7.x86_64.rpm

RUN yum --assumeyes install \
        kmod-lustre-client-${LUSTRE_VERSION}*.rpm \
        lustre-client-${LUSTRE_VERSION}*.rpm \
        lustre-client-devel-${LUSTRE_VERSION}*.rpm

COPY *.repo /etc/yum.repos.d/

COPY mero.spec .
RUN sed -i 's/@.*@/111/g' mero.spec
RUN kernel_src=$(ls -1rd /lib/modules/*/build | head -n1) \
    yum-builddep -y mero.spec

RUN rm -f mero.spec
