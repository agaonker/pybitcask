#!/bin/bash

for i in {1..1000}; do
    pbc put name "Ashish"
    echo "Put $i/1000"
done
