#!/bin/bash

cd /afs/cern.ch/work/z/zhixing/private/CMSSW_10_2_13/src/

eval `scram runtime -sh`

cd /afs/cern.ch/work/z/zhixing/private/CMSSW_10_3_3/src/Zprime_to_bb/run2_data

masses=(1600 1700 1800 1900 2000 2100 2200 2300 2400 2500 2600 2700 2800 2900 3000 3100 3200 3300 3400 3500 3600 3700 3800 3900 4000 4100 4200 4300 4400 4500 4600 4700 4800 4900 5000 5100 5200 5300 5400 5500 5600 5700 5800 5900 6000 6100 6200 6300 6400 6500 6600 6700 6800 6900 7000 7100 7200 7300 7400 7500 7600 7700 7800 7900 8000)

mass_nr=$1

mass=${masses[${mass_nr}]}
inputfile=../datacards/medium/bstar/combined/fully_combined_run2_M${mass}.txt
tmp_stdout=data_run2_${mass}.txt
outfile=../combine/limits/bstar/medium/combined_run2/fully_combined_run2_M${mass}.txt

combine -M AsymptoticLimits -d $inputfile -m $mass > $tmp_stdout

cat $tmp_stdout | grep -e Observed -e Expected | awk '{print $NF}' >> $outfile
