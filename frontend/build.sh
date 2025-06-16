#!/bin/bash

# Set environment variables for the build
export GENERATE_SOURCEMAP=false
export ESLINT_NO_DEV_ERRORS=true
export CI=false

# Run the build command
npm run build

# Exit with the build command's exit code
exit $?
