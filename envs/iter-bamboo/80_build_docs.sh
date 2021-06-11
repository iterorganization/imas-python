#!/bin/sh
# Build HTML pages from source
set -e
my_dir=$(dirname $0)

make -C docs html
