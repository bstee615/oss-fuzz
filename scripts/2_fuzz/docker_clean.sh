docker ps -f ancestor=gcr.io/oss-fuzz-base/base-runner -q | xargs docker rm -f 2>/dev/null
