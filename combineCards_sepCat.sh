#!/bin/bash

###
### Macro for combining the datacards for separate categories into a single one for each mass point.
###

########## input arguments ########## 
btagging=$1
category=$2  #bq, bb, mumu
#####################################

cd datacards/$btagging

if [[ $category == bb || $category == bq ]]; then
    cat_len=7
elif [[ $category == mumu ]]; then
    cat_len=9
else
    echo "unknown category! aborting!!"
    exit
fi
let cat_len2=$cat_len+2

for card_2016 in ${category}_2016_M*.txt; do
    mass="${card_2016:$cat_len2:4}"
    let n=${#card_2016}-$cat_len
    suffix="${card_2016:$cat_len:$n}"
    card_2017="${category}_2017${suffix}"
    card_2018="${category}_2018${suffix}"

    ncards=0
    for card in $card_2016 $card_2017 $card_2018; do
        if test -f "$card"; then
            let ncards=$ncards+1
        fi
    done
    if [[ $ncards -eq 3 ]]; then
        echo "input datacards:"
        echo "1) datacards/${btagging}/${card_2016}"
        echo "2) datacards/${btagging}/${card_2017}"
        echo "3) datacards/${btagging}/${card_2018}"
        echo "output datacard: datacards/${btagging}/${category}_combined_run2${suffix}"
        combineCards.py ${category}_2016="$card_2016" ${category}_2017="$card_2017" ${category}_2018="$card_2018" > "${category}_combined_run2${suffix}"
    else
        echo "only ${ncards} could be associated to ${card_2016}"
    fi

done


cd ../..

