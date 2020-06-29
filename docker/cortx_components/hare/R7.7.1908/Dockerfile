FROM ssc-vm-0007.colo.seagate.com:5000/rhel_mero:7.7.1908

ENV HARE_VENV_DIR=$HOME/.hare-venv

RUN yum install -y python36 python36-devel python36-pip python36-PyYAML
RUN mkdir $HARE_VENV_DIR \
    && python3 -m venv $HARE_VENV_DIR

# PyYAML - for cfgen
# flake8 - for hax
# mypy   - for hax
# ply    - for Mero
# wheel  - for hax
RUN source $HARE_VENV_DIR/bin/activate \
    && pip3 install PyYAML flake8 mypy ply wheel

ADD https://github.com/dhall-lang/dhall-haskell/releases/download/1.26.1/dhall-1.26.1-x86_64-linux.tar.bz2      /var/cache
ADD https://github.com/dhall-lang/dhall-haskell/releases/download/1.26.1/dhall-json-1.4.1-x86_64-linux.tar.bz2  /var/cache
RUN for f in /var/cache/dhall*.tar*; do tar -C /usr/local -xf $f; done

COPY docker-entrypoint /usr/local/bin/

 RUN yum clean all \
    && rm -rf /var/cache/yum
