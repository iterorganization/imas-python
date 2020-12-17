#!/bin/sh
# Pip install dependencies and build sdist and wheel
$PIP install --user --ignore-installed pip setuptools
$PIP install --upgrade $build_deps

# install rundeps into local install folder
for file in $run_dep_files; do
    echo Installing $file
    $PIP install -r $file
done

make sdist wheel
