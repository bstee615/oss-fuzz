#!/bin/bash
PROJECT="$1"
echo N | python3 infra/helper.py build_image $PROJECT
python3 infra/helper.py build_fuzzers --sanitizer address --architecture x86_64 $PROJECT
