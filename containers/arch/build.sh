#!/usr/bin/env bash
git clone ssh://git@git.iter.org/imas/data-dictionary.git
cd data-dictionary
git checkout saxon-cmd

cd ..
git clone ssh://git@git.iter.org/imas/access-layer.git
cd access-layer
git checkout develop
