#!/bin/bash

#./Signal_Fitter.py -y 2016 -b medium &  
#./Signal_Fitter.py -y 2017 -b medium &
#./Signal_Fitter.py -y 2018 -b medium &
#./Signal_Fitter.py -y run2 -b medium &
#wait

#./Signal_Fitter.py -y 2016 -b loose &  
./Signal_Fitter.py -y 2017 -b loose &
./Signal_Fitter.py -y 2018 -b loose &
./Signal_Fitter.py -y run2 -b loose &
wait
