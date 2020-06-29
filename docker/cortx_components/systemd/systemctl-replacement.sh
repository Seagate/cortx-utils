#!/bin/bash

wget https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/master/files/docker/systemctl.py
cp /usr/bin/systemctl /usr/bin/systemctl.bak    # Keep a backup of systemctl in case we mess up
yes | cp -f systemctl.py /usr/bin/systemctl
chmod a+x /usr/bin/systemctl
#test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl
