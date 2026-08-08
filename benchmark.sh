#!/usr/bin/env bash

set -u

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "========================================"
echo "FORGE PERFORMANCE BENCHMARK"
echo "========================================"
echo

echo "Version:"
./FORGE --version

echo
echo "System:"
uname -srmo

echo
echo "Python:"
python3 --version

echo
echo "----------------------------------------"
echo "1,000 candidates"
echo "----------------------------------------"

rm -f /tmp/forge-benchmark-1000.txt

time ./FORGE \
    --mode exhaustive \
    --traversal sequential \
    --length 4 \
    --limit 1000 \
    --keyword ab \
    --output /tmp/forge-benchmark-1000.txt

echo
echo "Output:"
wc -l /tmp/forge-benchmark-1000.txt
ls -lh /tmp/forge-benchmark-1000.txt

echo
echo "----------------------------------------"
echo "10,000 candidates"
echo "----------------------------------------"

rm -f /tmp/forge-benchmark-10000.txt

time ./FORGE \
    --mode exhaustive \
    --traversal sequential \
    --length 4 \
    --limit 10000 \
    --keyword ab \
    --output /tmp/forge-benchmark-10000.txt

echo
echo "Output:"
wc -l /tmp/forge-benchmark-10000.txt
ls -lh /tmp/forge-benchmark-10000.txt

echo
echo "========================================"
echo "BENCHMARK COMPLETE"
echo "========================================"
