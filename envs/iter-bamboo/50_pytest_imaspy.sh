#!/bin/sh
# Test installed package

if [ "$1" == "mini" ]; then
				make minitests
else
				make tests
fi
