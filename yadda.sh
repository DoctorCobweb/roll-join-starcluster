#!/bin/bash

#use must first export AWS access key and secret access key to use s3 
export JOIN_FILE_INDEX=$1

cd /root
python /roll_data/roll-join/spatial_join/spatial_join.py
