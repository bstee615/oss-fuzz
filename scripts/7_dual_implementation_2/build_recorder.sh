#!/bin/bash
(cd recorder && ./gradlew build jar)
cp recorder/lib/build/libs/recorder-1.0.0.jar infra/base-images/base-builder-jvm/recorder-1.0.0.jar
cp recorder/lib/build/libs/recorder-1.0.0.jar infra/base-images/base-runner/recorder-1.0.0.jar

touch infra/base-images/base-builder-jvm/recorder-1.0.0.jar
touch infra/base-images/base-runner/recorder-1.0.0.jar

(cd infra/base-images/base-builder-jvm && docker build -f Dockerfile.recorder --no-cache -t gcr.io/oss-fuzz-base/base-builder-jvm:recorder-1.0.0 .)
(cd infra/base-images/base-runner      && docker build -f Dockerfile.recorder --no-cache -t gcr.io/oss-fuzz-base/base-runner:recorder-1.0.0 .)
