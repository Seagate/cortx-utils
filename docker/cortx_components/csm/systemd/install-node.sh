#!/bin/bash


NODE_VERSION=$1

if [ -z $NODE_VERSION ]; then
echo "Node version is not provided. exiting.."
exit 1
fi

curl https://raw.githubusercontent.com/creationix/nvm/v0.33.11/install.sh -o $PWD/install.sh && sh $PWD/install.sh

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && source "$NVM_DIR/bash_completion"
echo "Installing Node $NODE_VERSION"
nvm install $1
