#! /usr/bin/env python

###
### Macro for skimming the weighted ntuples heavily to a compact size.
###

import global_paths
import os
from array import array
from ROOT import TFile, TChain, TTree, TH1, TH1F, TObject
from aliases import triggers

#inDir = global_paths.WEIGHTEDDIR[:-1]
#outDir = global_paths.SKIMMEDDIR[:-1]
inDir = global_paths.PRODUCTIONDIR[:-1] 
outDir = global_paths.WEIGHTEDDIR[:-1]

blacklist = ["backup","weighted","parallel_execution"]
cutstring = "jj_mass_widejet>1530 && "+triggers

def skim(sample):
    print sample
    fileList = os.listdir(inDir+"/"+sample)
    if len(fileList)==0: return
    print fileList
    chain = TChain("tree")
    events_hist = TH1F('Events', 'Events', 1,0,1)
    for f in fileList:
        chain.Add(inDir+"/"+sample+"/"+f)
        print chain.GetNtrees(), chain.GetEntries(), inDir+"/"+sample+"/"+f
        fl = TFile(inDir+"/"+sample+"/"+f, "READ")
        events_hist.Add(fl.Get("Events"))
        fl.Close()
    #return
    
    
    # save to new file
    outFile = TFile(outDir+"/"+sample+".root", "RECREATE")
    outFile.cd()
    # create a new skimmed tree
    tree = chain.CopyTree(cutstring)#GetTree().CloneTree(-1, cutstring)
    tree.Write("", TObject.kOverwrite)
    events_hist.Write()
    outFile.Close()

    chain.Reset()


#dirList = [x for x in os.listdir(inDir) if not x in blacklist and not 'SingleMuon' in x]
#dirList = [x for x in os.listdir(inDir) if (('data' in x and ('2017' in x and 'B' not in x and 'C' not in x) or ('2018' in x)) )]
dirList = [x for x in os.listdir(inDir)]
for d in dirList:
  if ('2016' in d  and 'bstar' in d) and os.path.isdir(inDir+'/'+d):
    print d
    skim(d)
