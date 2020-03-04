#!/bin/bash

###
### Macro for combining the datacards of all run2 years for separate categories into a single one for each mass point.
###

########## input arguments ########## 
btagging=$1
#####################################

cd datacards/MANtag_study/$btagging

for card_2016_bb in bb_2016_M*.txt; do
    mass="${card_2016_bb:9:4}"
    let n=${#card_2016_bb}-7
    suffix="${card_2016_bb:7:$n}"
    #card_2016_bq="bq_2016${suffix}"
    #card_2016_mumu="mumu_2016${suffix}"
    card_2017_bb="bb_2017${suffix}"
    #card_2017_bq="bq_2017${suffix}"
    #card_2017_mumu="mumu_2017${suffix}"
    card_2018_bb="bb_2018${suffix}"
    #card_2018_bq="bq_2018${suffix}"
    #card_2018_mumu="mumu_2018${suffix}"

    ncards=0
    #for card in $card_2016_bb $card_2016_bq $card_2016_mumu $card_2017_bb $card_2017_bq $card_2017_mumu $card_2018_bb $card_2018_bq $card_2018_mumu; do
    for card in $card_2016_bb $card_2017_bb $card_2018_bb; do
        if test -f "$card"; then   
            let ncards=$ncards+1
        fi
    done
    if [[ $ncards -eq 3 ]]; then
        echo "input datacards:"
        echo "1) datacards/MANtag_study/${btagging}/${card_2016_bb}"
        #echo "2) datacards/MANtag_study/${btagging}/${card_2016_bq}"
        #echo "3) datacards/MANtag_study/${btagging}/${card_2016_mumu}"
        echo "4) datacards/MANtag_study/${btagging}/${card_2017_bb}"
        #echo "5) datacards/MANtag_study/${btagging}/${card_2017_bq}"
        #echo "6) datacards/MANtag_study/${btagging}/${card_2017_mumu}"
        echo "7) datacards/MANtag_study/${btagging}/${card_2018_bb}"
        #echo "8) datacards/MANtag_study/${btagging}/${card_2018_bq}"
        #echo "9) datacards/MANtag_study/${btagging}/${card_2018_mumu}"
        echo "output datacard: datacards/MANtag_study/${btagging}/combined/fully_combined_run2${suffix}"
        #combineCards.py bb_2016="$card_2016_bb" bq_2016="$card_2016_bq" mumu_2016="$card_2016_mumu" bb_2017="$card_2017_bb" bq_2017="$card_2017_bq" mumu_2017="$card_2017_mumu" bb_2018="$card_2018_bb" bq_2018="$card_2018_bq" mumu_2018="$card_2018_mumu" > "combined/fully_combined_run2${suffix}"
        combineCards.py bb_2016="$card_2016_bb" bb_2017="$card_2017_bb" bb_2018="$card_2018_bb" > "combined/fully_combined_run2${suffix}"
    else
        echo "only ${ncards} could be associated to ${card_2016_bb}"
    fi

done

cd ../..

