#!/bin/bash

# Start the first process
# ./worker/start.sh &

# Start the second process
./server/start.sh &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
