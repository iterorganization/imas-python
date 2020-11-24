#!/usr/bin/env bash
git clone ssh://git@git.iter.org/imas/data-dictionary.git

git clone ssh://git@git.iter.org/imas/access-layer.git

git clone ssh://git@gitlab.com/klimex/imaspy.git

docker build .
