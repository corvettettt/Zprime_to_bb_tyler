#!/bin/bash

###
### Macro for running the combine tool locally for each mass point, merely on a single category.
###

## fetiching global variables
main_dir='./'        #to be replaced when submitted to HTCondor. Currently has to be on line 8 to be correctly replaced in submit_combine.py!
echo "main_dir = ${main_dir}"
combine_dir=$(${main_dir}global_paths.py -g COMBINEDIR)
echo "combine_dir = ${combine_dir}"
grid_cert=$(${main_dir}global_paths.py -g GRIDCERT)
echo "grid_cert = ${grid_cert}"

echo
echo
echo 'START---------------'
workdir=$(pwd)
echo "workdir = $workdir"
#cd /afs/cern.ch/user/m/msommerh/CMSSW_10_2_13/src/HiggsAnalysis/CombinedLimit
cd $combine_dir
eval `scram runtime -sh`
cd $workdir

#export X509_USER_PROXY=/afs/cern.ch/user/m/msommerh/x509up_msommerh
export X509_USER_PROXY=$grid_cert
use_x509userproxy=true


#option=""

masses=(1200 1300 1400 1500 1600 1700 1800 1900 2000 2100 2200 2300 2400 2500 2600 2700 2800 2900 3000 3100 3200 3300 3400 3500 3600 3700 3800 3900 4000 4100 4200 4300 4400 4500 4600 4700 4800 4900 5000 5100 5200 5300 5400 5500 5600 5700 5800 5900 6000 6100 6200 6300 6400 6500 6600 6700 6800 6900 7000 7100 7200 7300 7400 7500 7600 7700 7800 7900 8000)

########## input arguments ########## 
isMC=$1
year=$2
btagging=$3
mass_nr=$4
category=$5
#####################################

mass=${masses[${mass_nr}]}

echo "isMC = ${isMC}"
echo "year = ${year}"
echo "btagging = ${btagging}"
echo "mass_nr = ${mass_nr}"
echo "mass = ${mass}"

if [[ $isMC -eq 1 ]]; then
    echo "running purely on MC..."
    suffix="_MC.txt"
else
    echo "running on real data..."
    suffix=".txt"
fi


## setting up a repository structure on the local working node:

mkdir datacards
mkdir datacards/${btagging}
mkdir workspace
mkdir workspace/${btagging}

#cp /afs/cern.ch/user/m/msommerh/CMSSW_10_3_3/src/NanoTreeProducer/datacards/${btagging}/${category}_${year}_M${mass}${suffix} datacards/${btagging}/
#cp /afs/cern.ch/user/m/msommerh/CMSSW_10_3_3/src/NanoTreeProducer/workspace/${btagging}/MC_signal_${year}* workspace/${btagging}/
#cp /afs/cern.ch/user/m/msommerh/CMSSW_10_3_3/src/NanoTreeProducer/workspace/${btagging}/${prefix}_${year}* workspace/${btagging}/
cp ${main_dir}datacards/${btagging}/${category}_${year}_M${mass}${suffix} datacards/${btagging}/
cp ${main_dir}workspace/${btagging}/MC_signal_${year}* workspace/${btagging}/
cp ${main_dir}workspace/${btagging}/${prefix}_${year}* workspace/${btagging}/

echo "ls datacards/${btagging}/"
ls datacards/${btagging}/
echo "ls workspace/${btagging}/"
ls workspace/${btagging}/


inputfile=datacards/${btagging}/${category}_${year}_M${mass}${suffix}
#outputfile="/afs/cern.ch/user/m/msommerh/CMSSW_10_3_3/src/NanoTreeProducer/combine/limits/${btagging}/single_category/"
outputfile="${main_dir}combine/limits/${btagging}/single_category/"
#tempfile=$(echo $inputfile | sed s:/afs/cern.ch/user/m/msommerh/CMSSW_10_3_3/src/NanoTreeProducer/datacards/${btagging}/:${workdir}/:g)
tempfile=$(echo $inputfile | sed s:${main_dir}datacards/${btagging}/:${workdir}/:g)
echo "inputfile = ${inputfile}"
echo "outputfile = ${outputfile}"
echo "tempfile = ${tempfile}"

> $tempfile

#echo "combine -M AsymptoticLimits -d ${inputfile} -m ${mass} | grep -e Observed -e Expected | awk '{print ${NF}}' >> ${tempfile}"
#combine -M AsymptoticLimits -d $inputfile -m $mass | grep -e Observed -e Expected | awk '{print $NF}' >> $tempfile
echo "combine -M AsymptoticLimits -d $inputfile -m $mass > tmp_stdout.txt"
combine -M AsymptoticLimits -d $inputfile -m $mass > tmp_stdout.txt
echo
echo
echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo "combine output:"
echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo
cat tmp_stdout.txt
echo
echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo
echo
echo "cat tmp_stdout.txt | grep -e Observed -e Expected | awk '{print $NF}' >> $tempfile"
cat tmp_stdout.txt | grep -e Observed -e Expected | awk '{print $NF}' >> $tempfile


cp $tempfile $outputfile
echo "output copied to afs"

rm higgsCombine*.root
rm roostats-*
rm mlfit*.root

echo "all clear"

echo
echo
echo 'END ----------------'
echo
echo

