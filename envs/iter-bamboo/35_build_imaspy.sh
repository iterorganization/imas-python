#!/bin/sh
# Build IMASPy dists and wheel

export build_deps=$(cat pyproject.toml | grep requires | cut -d'=' -f2- | tr -d ,\"\' | sed "s/^ \[//" | sed "s/\]$//")
export test_deps=$(find . -maxdepth 1 -and -name "requirements_test*")

# Pip install build dependencies
$PIP install --target=$PYTHON_INSTALL_DIR --ignore-installed pip setuptools
$PIP install --target=$PYTHON_INSTALL_DIR --upgrade $build_deps

# install rundeps into local install folder
# Install run dependencies in local install folder
export run_dep_files=$(find . -maxdepth 1 -and -not -name "*test*" -and -not -name "*backends_al*" -and -not -name "*examples*" -and -name 'requirements_*')
for file in $run_dep_files; do
    echo Installing $file
    $PIP install --target=$PYTHON_INSTALL_DIR -r $file
done

make sdist wheel
