#!/bin/bash

../espresso.linux $1 | ./vgen.py $2 ${3:-"MODULE_NAME"}
cat $2
echo