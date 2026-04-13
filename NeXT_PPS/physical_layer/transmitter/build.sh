#!/usr/bin/env bash
set -e

BUILD_DIR="build"

if [ ! -d "$BUILD_DIR" ]; then
    mkdir -p "$BUILD_DIR"
fi

cd "$BUILD_DIR"

if [ ! -f "CMakeCache.txt" ]; then
    cmake ..
fi

cmake --build . -- -j8

echo "Build complete."
