#!/bin/bash

grep '^FUZZER_OUTPUT_JSONL' | head -n-1 | tail -n+2 | sed 's/^FUZZER_OUTPUT_JSONL //g'
