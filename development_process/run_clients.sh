#!/bin/bash



for run in {1..8}
do
  python3 client_v2.py &
done

exit 0