#!/bin/bash

masses=(1600 1700 1800 1900 2000 2100 2200 2300 2400 2500 2600 2700 2800 2900 3000 3100 3200 3300 3400 3500 3600 3700 3800 3900 4000 4100 4200 4300 4400 4500 4600 4700 4800 4900 5000 5100 5200 5300 5400 5500 5600 5700 5800 5900 6000 6100 6200 6300 6400 6500 6600 6700 6800 6900 7000 7100 7200 7300 7400 7500 7600 7700 7800 7900 8000)

for i in "${masses[@]}"
  do
    for j in 2016 2017 2018 
      do 
        cat ${j}/MC${j}${i}.txt | grep -e Observed -e Expected | awk '{print $NF}' >> combine/limits/bstar/medium/${j}_M${i}_MC.txt
	cat ${j}_data/data${j}${i}.txt | grep -e Observed -e Expected | awk '{print $NF}' >> combine/limits/bstar/medium/${j}_M${i}.txt
   
      done
    cat run2/MC_run2_${i}.txt | grep -e Observed -e Expected | awk '{print $NF}' >> combine/limits/bstar/medium/combined_run2/run2_M${i}_MC.txt
    cat run2_data/data_run2_${i}.txt | grep -e Observed -e Expected | awk '{print $NF}' >> combine/limits/bstar/medium/combined_run2/run2_M${i}.txt
  done 
