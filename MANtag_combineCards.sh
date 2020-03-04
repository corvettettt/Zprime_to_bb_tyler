#!/bin/bash

###
### Macro for combining the datacards for separate categories into a single one for each mass point.
###

########## input arguments ########## 
btagging=$1
#####################################

cd datacards/MANtag_study/$btagging

for card1 in bb_*.txt
do
    let n=${#card1}-2
    mv $card1 "combined/combined${card1:2:$n}"
done

cd ../..

