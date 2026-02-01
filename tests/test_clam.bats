#!/usr/bin/env bats

setup() {
    # Install clam.sh from parent directory
    bash "$BATS_TEST_DIRNAME/../install.sh"

    # Source bashrc to make sure clam is available in the current session
    source ~/.bashrc

    # Assert CLAM_OPENAI_API_KEY is set
    if [ -z "$CLAM_OPENAI_API_KEY" ]; then
        echo "ERROR: CLAM_OPENAI_API_KEY is not set. Please set the environment variable before running the tests."
        exit 1
    fi
}

teardown() {
    clam model openai gpt-4o
}

@test "which clam returns something" {
    run which clam
    [ "$status" -eq 0 ]
    [ -n "$output" ]
}

@test "clam returns a string containing clam.sh (case insensitive)" {
    run clam
    [ "$status" -eq 0 ]
    [[ "$output" =~ [Cc]lam\.sh ]]
}

@test "clam model gpt4o-mini and then config should have the string gpt4o-mini" {
    # Set the model and capture status
    run clam model openai gpt-4o-mini
    [ "$status" -eq 0 ]
    [[ "$output" =~ gpt-4o-mini ]]

    # Check that config file was updated
    run grep "^model:" ~/.clam/config
    [ "$status" -eq 0 ]
    [[ "$output" =~ gpt-4o-mini ]]
}

@test "clam command 'ls # show largest files' should return something" {
    run clam command "ls # show largest files"
    [ "$status" -eq 0 ]
    [ -n "$output" ]
}
