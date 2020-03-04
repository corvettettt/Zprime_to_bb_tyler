#!/bin/bash

###
### Macro for running the combine tool locally for each mass point.
###

option=""

higgsCombine() {
    inputfile=$1
    outputfile=$2
    lower_mass=$3
    upper_mass=$4
    mass=$(echo $inputfile | sed s/2016// | sed s/2017// | sed s/2018// | sed s/run2// |tr -dc '0-9') #delete every character except the numbers. First removes the year

    if [[ $lower_mass -lt 1600 ]]
    then lower_mass=1599
    fi

    if [[ $mass -gt $lower_mass ]] && [[ $mass -le $upper_mass ]]; then
        echo "Input file: ${inputfile}; Output file: ${outputfile}"
        > $outputfile
        #if echo "$option" | grep -q "blind"; then 
        #  echo '1' >> $outputfile
        #fi
        combine -M AsymptoticLimits -d $inputfile -m $mass | grep -e Observed -e Expected | awk '{print $NF}' >> $outputfile #i.e. take the output of combine, select the lines containing "Observed" and "Expected" via grep, select the last field via awk and append it to the outputfile
    fi
}

########## input arguments ########## 
btagging=$1
year=$2
isMC=$3
category=$4
#####################################

if [[ $year == run2c ]]; then
    echo "Combining the 2016-2018 fits separately into a single limit..."
    year="run2"
    combined=1
else
    combined=0
fi

if [[ $isMC -eq 1 ]]; then
    echo "running purely on MC..."
    suffix="0_MC.txt"
else
    suffix="0.txt"
fi

for low_mass in 1000 2000 3000 4000 5000 6000 7000; do
    let high_mass=$low_mass+1000

    echo "low_mass=${low_mass}, high_mass=${high_mass}"

    if [[ $combined -eq 1 ]]; then
        for card in datacards/${btagging}/${category}_combined_run2_*${suffix}; do
            output=$(echo $card | sed s:datacards/:combine/limits/: | sed s:combined_:: | sed s:${btagging}/:${btagging}/single_category/combined_run2/:)
            higgsCombine $card $output $low_mass $high_mass &
        done
    else
        for card in datacards/${btagging}/${category}_${year}_*${suffix}; do
            output=$(echo $card | sed s:datacards/:combine/limits/: | sed s:${btagging}/:${btagging}/single_category/:)
            higgsCombine $card $output $low_mass $high_mass &
        done
    fi
    wait
done

## Clean
wait

rm higgsCombine*.root
rm roostats-*
rm mlfit*.root

echo -e "\e[00;32mAll clear\e[00m"

