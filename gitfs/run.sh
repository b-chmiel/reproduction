#!/bin/bash

set -euo

cp ./patches/*.patch source/
pushd source
    git am *.patch
    vagrant destroy -f 
    vagrant up
    vagrant ssh -- -t <<HEREDOC
cd /vagrant
sudo bash test.sh
HEREDOC

    vagrant destroy -f
popd
cp -R ./source/out ./out/
