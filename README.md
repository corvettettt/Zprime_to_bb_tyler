# Installation

First, install the NanoAOD tools:
```
export SCRAM_ARCH=slc6_amd64_gcc700
cmsrel CMSSW_10_3_3
cd CMSSW_10_3_3/src
cmsenv
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
scram b
```
Then clone this repository:
```
git clone https://github.com/msommerh/Zprime_to_bb Zprime_to_bb
cd Zprime_to_bb
source setupEnv.sh
```

Install combine according to the manual:
http://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/#cc7-release-cmssw_10_2_x-recommended-version

Set the desired paths in *global_paths.py*

For every new shell session, do
```
cd CMSSW_10_3_3/src
cmsenv
cd Zprime_to_bb
source setupEnv.sh
```

for HTCondor submission, get the GRID certificate, find its location and put the path into *global_paths.py*:
```
voms-proxy-init --voms cms --valid 200:00
echo $(voms-proxy-info -path)
```



# Ntuple production

## deduce b-tagging weights for the signal:

[year]: 2016, 2017, 2018;   [btagging]: tight, medium, loose

create histograms for each year/masspoint of tagged and untagged jets directly fron the NanoAOD signal files:
```
./postprocessors/BTaggingEfficiency.py -mp
```
output in *btag/MC_signal_histst/*

evaluate the btagging efficiency in each year:
```
./getBTagEfficiencies.py -y 2016 2017 2018 -w [btagging] -p
```
output in *btag/*

## submit the samples:   

[year]: 2016, 2017, 2018

MC signal:
```
./submit.py -q workday -y [year] -MC -MT signal
```
MC background:     [MC_type]: QCD, TTbar
```
./submit.py -q workday -y [year] -MC -MT [MC_type] -n 1 -mn
```
data:
```
./submit.py -q workday -y [year] -n 1 -mn
```
single muon data (trigger efficiency study):
```
./submit.py -q workday -y [year] -n 1 -mn -Tr
```


## check if the samples have finished correctly:
```
./check_submission.sh
```
resubmit erroneous samples by putting the sample name in the corresponding file in *resubmission/resubmit_[sample_name]* and run:
```
./submit.py [same options as original submission (or slightly adjusted)] -rs resubmission/resubmit_[sample_name]
```
if the submission only crashes on a single file, identify the file nr from the stdout and resubmit via:
```
./submit.py [same options as original submission] -rs resubmission/resubmit_[sample_name] -rf [file_nr]
```

output in: *global_paths.PRODUCTIONDIR*


## Postprocess samples

### skim the samples:
```
./postprocessors/skim.py
```
output in *global_paths.WEIGHTEDDIR*

trigger study:
```
./postprocessors/skim_SingleMuon.py
```
output in *global_paths.SKIMMEDDIR/TriggerStudy*

### add weights, even to the data and MC signal:    

[year]: 2016, 2017, 2018;   [MC_type]: signal, QCD, TTbar
```
./postprocessors/addWeights.py -y [year] -MC -MT [MC_type]
./postprocessors/addWeights.py -y [year] 
```

output in *global_paths.SKIMMEDDIR*

### deduce btagging uncertainty
```
./postprocessors/BTaggingUncertainties.py -b [btagging]
```
output directly written into *BTag_uncertainties.py*, which is imported by *samples.py*



# Various plots

## plot MC/data comparison

plot all relevant variable distributions:
```
Plot_all.sh all
```
output in: *plots/[preselection, 1b, 2b]/*

## signal acceptance, trigger efficiency and signal efficiency

[year]: 2016, 2017, 2018

extract genParticle information from NanoAOD by running:
```
postprocessors/Acceptance.py -y [year] -mp
```
output in *acceptance/*

then plot acceptance as a function of mass points:
```
Plot_all.sh acc
```

plot the trigger efficiency:
```
Plot_all.sh trig
```

and plot the efficiency:
```
Plot_all.sh eff
```

output in: *plots/Efficiency*



# Fits and limits extraction

## apply fit on QCD_TTbar/data and signal

 [year]: 2016, 2017, 2018, run2;   [btagging]: tight, medium, loose

fit on the MC signal: 
```
./Signal_Fitter.py -y [year] -b [btagging]
```
before running the signal fits for the first time, one might need to load the signal model:
```
cd PDFs/
root -l
.L HWWLVJRooPdfs.cxx++
.q 
cd ..
```

fit on MC background:
```
./Bkg_Fitter.py -y [year] -M -b [btagging]
```

fit on data: (currently not advised until blinding implemented or explicitly allowed)

~~`./Bkg_Fitter.py -y [year] -b [btagging]`~~


output in:

plots: *plots/[btagging]/[data_type]_[year]/*

workspace: *workspace/[btagging]/*


## create datacards

(works independently of the actual fits)

[year]: 2016, 2017, 2018, run2;   [btagging]: tight, medium, loose

MC:
```
./Datacards.py -M -y [year] -b [btagging]
```
data:
```
./Datacards.py -y [year] -b [btagging]
```
output in: *datacards/[btagging]/*

### combine cards of different btagging categories: 
(for this step, you first need to go to the combine tool directory and do *cmsenv*)
```
./combineCards.sh [btagging]
```
for running combine on run2 with fits in separate years:
```
./combineCards_run2.sh [btagging]
```
output in: *datacards/[btagging]/combined/*


## limits plots

[year]: 2016, 2017, 2018, run2, run2c (combining the fits of the three years separately);   [btagging]: tight, medium, loose

### run combine:

MC:
```
./submit_combine.py -MC -q longlunch -y [year] -b [btagging]
```
data: (currently not advised until blinding implemented or explicitly allowed)

~~`./submit_combine.py -q longlunch -y [year] -b [btagging]`~~

output in: *combine/limits/[btagging]/*

### plot the limits:

MC:
```
./limit.py -M -y [year] -b [btagging]
```
data: (currently not advised until blinding implemented or explicitly allowed)

~~`./limit.py -y [year] -b [btagging]`~~

output in: *combine/plotsLimit/*


