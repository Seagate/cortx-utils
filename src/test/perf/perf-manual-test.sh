#!/bin/bash

script_dir="$(readlink -f $(dirname $0))"
test_binary="/tmp/eos-fs/build-eos-utils/test/perf/perf-manual-test"
# reference output file
ref_output_file="$script_dir/perf-manual-test.output.txt"

verify() {
    "$test_binary" > /tmp/actual
    cp "$ref_output_file" /tmp/expected
    diff -u /tmp/expected /tmp/actual
    rc=$?

    if ((rc == 0)); then
        echo "OK"
    fi

    return $rc
}

update() {
    "$test_binary" > /tmp/actual
    cp /tmp/actual "$ref_output_file"
    echo "Done"
    return 0
}

case $1 in
    update)
        update;;
    verify)
        verify;;
    *)
        echo "Use 'verify' or 'update' commands";;
esac
