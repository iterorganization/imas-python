#!/bin/sh
# Set up user-like IMAS env
set -e

# Use the parts of IMAS
module load Python/3.6.4-intel-2018a
module load Cython/0.28.6-intel-2018a-Python-3.6.4

# But for now import IMAS itself
# TODO: Move to split repo
module load IMAS
