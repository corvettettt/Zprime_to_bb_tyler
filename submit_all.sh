#!/bin/bash

#./submit.py -q workday -y 2016 -MC -MT signal
#./submit.py -q workday -y 2017 -MC -MT signal
#./submit.py -q workday -y 2018 -MC -MT signal
#
#./submit.py -q workday -y 2016 -MC -MT QCD -n 1 -mn
#./submit.py -q workday -y 2016 -MC -MT TTbar -n 1 -mn
#./submit.py -q workday -y 2017 -MC -MT QCD -n 1 -mn
#./submit.py -q workday -y 2017 -MC -MT TTbar -n 1 -mn
#./submit.py -q workday -y 2018 -MC -MT QCD -n 1 -mn
#./submit.py -q workday -y 2018 -MC -MT TTbar -n 1 -mn

./submit.py -q tomorrow -y 2016 -n 1 -mn 
./submit.py -q tomorrow -y 2017 -n 1 -mn
./submit.py -q tomorrow -y 2018 -n 1 -mn 
#
#./submit.py -q workday -y 2016 -n 1 -mn -Tr 
#./submit.py -q workday -y 2017 -n 1 -mn -Tr
#./submit.py -q workday -y 2018 -n 1 -mn -Tr

