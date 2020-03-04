#!/bin/bash

#./Bkg_Fitter.py -M -y 2016 -b medium & 
#./Bkg_Fitter.py -M -y 2017 -b medium &
#./Bkg_Fitter.py -M -y 2018 -b medium &
#./Bkg_Fitter.py -M -y run2 -b medium &
#wait

#./Bkg_Fitter.py -y 2016 -b medium & 
#./Bkg_Fitter.py -y 2017 -b medium &
#./Bkg_Fitter.py -y 2018 -b medium &
#./Bkg_Fitter.py -y run2 -b medium &
#wait

./Bkg_Fitter.py -y 2016 -b loose & 
./Bkg_Fitter.py -y 2017 -b loose &
./Bkg_Fitter.py -y 2018 -b loose &
./Bkg_Fitter.py -y run2 -b loose &
wait
