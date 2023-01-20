#!/bin/bash
PROJECT="$1"
shift
python3 infra/helper.py build_fuzzers --sanitizer address --architecture x86_64 $PROJECT $@
