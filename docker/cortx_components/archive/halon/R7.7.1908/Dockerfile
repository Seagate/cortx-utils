#ARG  REDHAT_RELEASE
FROM 10.230.162.34:5000/rhel_mero:7.7.1908

ADD halon-dist.tar.gz .

COPY *.repo /etc/yum.repos.d/

RUN yum -y install \
           binutils-devel \
           gmp-devel \
           leveldb-devel \
           libgenders-devel \
           libyaml-devel \
           ncurses-devel \
           pcre-devel \
           stack

# ghc-options should match the defaults from `h0` script (see DEFAULT_GHC_OPTS)
#RUN cd halon \
#    && stack build --only-dependencies --ghc-options='-g -j2 -O0' \
#    && cd .. \
#    && rm -rf halon

# fix read permissions for some files that created with user-only access
#RUN find ~/.stack \! -perm -o=r -exec chmod a+r '{}' \; -print
