#!/bin/sh
# Build IMASPy dists and wheel


# Pip install build dependencies
$PIP install --user --ignore-installed pip setuptools
$PIP install --upgrade $build_deps

# install rundeps into local install folder
# Install run dependencies in local install folder
for file in $run_dep_files; do
    echo Installing $file
    $PIP install -r $file
done

make sdist wheel
