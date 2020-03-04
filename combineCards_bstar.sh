#!/bin/bash

###
### Macro for combining the datacards for separate categories into a single one for each mass point.
###

########## input arguments ########## 
btagging=$1
combineYears=$2 #set to 1 if the separate years should be combined into a full run2 fit
#####################################

cd datacards/$btagging

if [[ $combineYears -ne 1 ]]; then

    for card1 in bb_*.txt
    do
        mass="${card1:9:4}"
        let n=${#card1}-2
        card2="bq${card1:2:$n}"
        card3="mumu${card1:2:$n}"
        if test -f "$card2"; then
            if test -f "$card3"; then
                echo "input cards:"
                echo "1) datacards/${btagging}/bstar/${card1}"
                echo "2) datacards/${btagging}/bstar/${card2}"
                echo "3) datacards/${btagging}/bstar/${card3}" 
                echo "output card: datacards/${btagging}/bstar/combined/combined${card1:2:$n}"
                combineCards.py bb="$card1" bq="$card2" mumu="$card3" > "bstar/combined/combined${card1:2:$n}"
            else
                echo "datacards/${btagging}/${card3} does not exist"
            fi
        else
            echo "datacards/${btagging}/${card2} does not exist"
        fi
    done

else
    for card_2016_bb in bb_2016_M*.txt; do
        mass="${card_2016_bb:9:4}"
        let n=${#card_2016_bb}-7
        suffix="${card_2016_bb:7:$n}"
        card_2016_bq="bq_2016${suffix}"
        card_2016_mumu="mumu_2016${suffix}"
        card_2017_bb="bb_2017${suffix}"
        card_2017_bq="bq_2017${suffix}"
        card_2017_mumu="mumu_2017${suffix}"
        card_2018_bb="bb_2018${suffix}"
        card_2018_bq="bq_2018${suffix}"
        card_2018_mumu="mumu_2018${suffix}"
    
        ncards=0
        for card in $card_2016_bb $card_2016_bq $card_2016_mumu $card_2017_bb $card_2017_bq $card_2017_mumu $card_2018_bb $card_2018_bq $card_2018_mumu; do
            if test -f "$card"; then
                let ncards=$ncards+1
            fi
        done
        if [[ $ncards -eq 9 ]]; then
            echo "input datacards:"
            echo "1) datacards/${btagging}/bstar/${card_2016_bb}"
            echo "2) datacards/${btagging}/bstar/${card_2016_bq}"
            echo "3) datacards/${btagging}/bstar/${card_2016_mumu}"
            echo "4) datacards/${btagging}/bstar/${card_2017_bb}"
            echo "5) datacards/${btagging}/bstar/${card_2017_bq}"
            echo "6) datacards/${btagging}/bstar/${card_2017_mumu}"
            echo "7) datacards/${btagging}/bstar/${card_2018_bb}"
            echo "8) datacards/${btagging}/bstar/${card_2018_bq}"
            echo "9) datacards/${btagging}/bstar/${card_2018_mumu}"
            echo "output datacard: datacards/${btagging}/bstar/combined/fully_combined_run2${suffix}"
            combineCards.py bb_2016="$card_2016_bb" bq_2016="$card_2016_bq" mumu_2016="$card_2016_mumu" bb_2017="$card_2017_bb" bq_2017="$card_2017_bq" mumu_2017="$card_2017_mumu" bb_2018="$card_2018_bb" bq_2018="$card_2018_bq" mumu_2018="$card_2018_mumu" > "bstar/combined/fully_combined_run2${suffix}"
        else
            echo "only ${ncards} could be associated to ${card_2016_bb}"
        fi
    
    done

fi

cd ../..

