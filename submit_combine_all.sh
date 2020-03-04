#!/bin/bash

#./submit_combine.py -MC -q longlunch -y run2c -b medium
#./submit_combine.py -MC -q longlunch -y run2 -b medium
#./submit_combine.py -MC -q longlunch -y 2018 -b medium
#./submit_combine.py -MC -q longlunch -y 2017 -b medium
#./submit_combine.py -MC -q longlunch -y 2016 -b medium

#./submit_combine.py -q longlunch -y run2c -b medium
#./submit_combine.py -q longlunch -y run2 -b medium
#./submit_combine.py -q longlunch -y 2018 -b medium
#./submit_combine.py -q longlunch -y 2017 -b medium
#./submit_combine.py -q longlunch -y 2016 -b medium

./submit_combine.py -q longlunch -y run2c -b loose
./submit_combine.py -q longlunch -y run2 -b loose 
./submit_combine.py -q longlunch -y 2018 -b loose
./submit_combine.py -q longlunch -y 2017 -b loose
./submit_combine.py -q longlunch -y 2016 -b loose
