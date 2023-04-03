#!/bin/bash
# Build the IMASPy documentation pages

. envs/iter-bamboo/iter-env.sh

pip install --no-build-isolation -v -e .[docs]

make -C docs html
