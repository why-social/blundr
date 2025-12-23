#!/bin/bash

mkdir -p build

for os in linux darwin windows; do
  for arch in amd64 arm64; do
    output="build/blundr-cli-${os}-${arch}"
    [[ $os == "windows" ]] && output+=".exe"

    echo "Building $output ..."
    
    GOOS=$os GOARCH=$arch go build -o "$output" main.go
  done
done