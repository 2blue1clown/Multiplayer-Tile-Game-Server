#!/bin/bash

for run in {1..4}
do
  python3 client.py &
done

exit 0