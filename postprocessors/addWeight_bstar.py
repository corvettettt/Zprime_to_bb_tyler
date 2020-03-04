#! /usr/bin/env python

###
### Macro for adding the correct weights to the primary ntuples.
###

import global_paths
import os, multiprocessing, math
import numpy as np
from array import array
from ROOT import TFile, TH1, TF1, TLorentzVector, TObject
import ROOT
import sys

from samples import sample as SAMPLE

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('-y', '--year', action='store', type=str, dest='year',default='2017')
parser.add_argument('-s', '--single', action='store_true', dest='single', default=False)
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False)
parser.add_argument("-MC", "--isMC", action="store_true", default=False, dest="isMC")
parser.add_argument('-MT', '--mcType',   dest='mcType', type=str, action='store', default="QCD", choices=['signal', 'QCD', 'TTbar','bstar'])
args = parser.parse_args()

singlecore  = args.single
verboseout  = args.verbose
year        = args.year
isMC        = args.isMC
mcType      = args.mcType

if year=='2016':
    LUMI=35920.
elif year=='2017':
    LUMI=41530.
elif year=='2018':
    LUMI=59740.


##############################

def getXsec(sample):
  print "Xsec("+sample+")"
  if sample.find( "QCD_Pt_170to300_"                       ) !=-1 : return 117276.;
  elif sample.find( "QCD_Pt_300to470_"                     ) !=-1 : return 7823.;
  elif sample.find( "QCD_Pt_470to600_"                     ) !=-1 : return 648.2;
  elif sample.find( "QCD_Pt_600to800_"                     ) !=-1 : return 186.9;
  elif sample.find( "QCD_Pt_1000to1400_"                   ) !=-1 : return 9.4183;
  elif sample.find( "QCD_Pt_1400to1800_"                   ) !=-1 : return 0.84265;
  elif sample.find( "QCD_Pt_1800to2400_"                   ) !=-1 : return 0.114943;
  elif sample.find( "QCD_Pt_2400to3200_"                   ) !=-1 : return 0.006830;
  elif sample.find( "QCD_Pt_3200toInf_"                    ) !=-1 : return 0.000165445;
  elif sample.find( "QCD_HT100to200"                       ) !=-1 : return 27990000;
  elif sample.find( "QCD_HT200to300"                       ) !=-1 : return 1712000.;
  elif sample.find( "QCD_HT300to500"                       ) !=-1 : return 347700.;
  elif sample.find( "QCD_HT500to700"                       ) !=-1 : return 32100.;
  elif sample.find( "QCD_HT700to1000"                      ) !=-1 : return 6831.;
  elif sample.find( "QCD_HT1000to1500"                     ) !=-1 : return 1207.;
  elif sample.find( "QCD_HT1500to2000"                     ) !=-1 : return 119.9;
  elif sample.find( "QCD_HT2000toInf"                      ) !=-1 : return 25.24;
  elif sample.find( "TTToHadronic"                         ) !=-1 : return 831.76*0.6741*0.6741;
  elif sample.find( "MC_signal_M"                       ) != -1 : return 1.;
  #elif sample.find( "MC_signal_M500"                       ) != -1 : return 170.378; 
  #elif sample.find( "MC_signal_M600"                       ) != -1 : return 85.0684;
  #elif sample.find( "MC_signal_M700"                       ) != -1 : return 46.9232;
  #elif sample.find( "MC_signal_M800"                       ) != -1 : return 27.7679;
  #elif sample.find( "MC_signal_M900"                       ) != -1 : return 17.3149;
  #elif sample.find( "MC_signal_M1000"                      ) != -1 : return 11.2428;
  #elif sample.find( "MC_signal_M1100"                      ) != -1 : return 7.53682;
  #elif sample.find( "MC_signal_M1200"                      ) != -1 : return 5.18495;
  #elif sample.find( "MC_signal_M1300"                      ) != -1 : return 3.64455;
  #elif sample.find( "MC_signal_M1400"                      ) != -1 : return 2.60813;
  #elif sample.find( "MC_signal_M1500"                      ) != -1 : return 1.89476;
  #elif sample.find( "MC_signal_M1600"                      ) != -1 : return 1.39466;
  #elif sample.find( "MC_signal_M1700"                      ) != -1 : return 1.03814;
  #elif sample.find( "MC_signal_M1800"                      ) != -1 : return 0.780036; 
  #elif sample.find( "MC_signal_M1900"                      ) != -1 : return 0.591187;
  #elif sample.find( "MC_signal_M2000"                      ) != -1 : return 0.451406;
  #elif sample.find( "MC_signal_M2100"                      ) != -1 : return 0.346939;
  #elif sample.find( "MC_signal_M2200"                      ) != -1 : return 0.26821;
  #elif sample.find( "MC_signal_M2300"                      ) != -1 : return 0.208423; 
  #elif sample.find( "MC_signal_M2400"                      ) != -1 : return 0.162712;
  #elif sample.find( "MC_signal_M2500"                      ) != -1 : return 0.127539;
  #elif sample.find( "MC_signal_M2600"                      ) != -1 : return 0.100341;
  #elif sample.find( "MC_signal_M2700"                      ) != -1 : return 0.0792067; 
  #elif sample.find( "MC_signal_M2800"                      ) != -1 : return 0.0627105;
  #elif sample.find( "MC_signal_M2900"                      ) != -1 : return 0.0498474;
  #elif sample.find( "MC_signal_M3000"                      ) != -1 : return 0.0395947;
  #elif sample.find( "MC_signal_M3100"                      ) != -1 : return 0.0315669;
  #elif sample.find( "MC_signal_M3200"                      ) != -1 : return 0.025215;
  #elif sample.find( "MC_signal_M3300"                      ) != -1 : return 0.0201745; 
  #elif sample.find( "MC_signal_M3400"                      ) != -1 : return 0.0161649;
  #elif sample.find( "MC_signal_M3500"                      ) != -1 : return 0.0129686;
  #elif sample.find( "MC_signal_M3600"                      ) != -1 : return 0.0104153;
  #elif sample.find( "MC_signal_M3700"                      ) != -1 : return 0.00837208; 
  #elif sample.find( "MC_signal_M3800"                      ) != -1 : return 0.00673479;
  #elif sample.find( "MC_signal_M3900"                      ) != -1 : return 0.00542162;
  #elif sample.find( "MC_signal_M4000"                      ) != -1 : return 0.0043664;
  #elif sample.find( "MC_signal_M4100"                      ) != -1 : return 0.00351863; 
  #elif sample.find( "MC_signal_M4200"                      ) != -1 : return 0.00283602;
  #elif sample.find( "MC_signal_M4300"                      ) != -1 : return 0.00228571;
  #elif sample.find( "MC_signal_M4400"                      ) != -1 : return 0.00184267;
  #elif sample.find( "MC_signal_M4500"                      ) != -1 : return 0.00148565;
  #elif sample.find( "MC_signal_M4600"                      ) != -1 : return 0.00119766;
  #elif sample.find( "MC_signal_M4700"                      ) != -1 : return 0.000965227;
  #elif sample.find( "MC_signal_M4800"                      ) != -1 : return 0.00077757;
  #elif sample.find( "MC_signal_M4900"                      ) != -1 : return 0.000626126;
  #elif sample.find( "MC_signal_M5000"                      ) != -1 : return 0.00050397;
  elif sample.find( "QCD_Pt-15to7000" ) !=-1 or sample.find( "QCD_Pt_15to7000" ) !=-1: return  2.022100000e+09;
  elif sample.find("SingleMuon")!=-1  or sample.find("SingleElectron") !=-1 or sample.find("JetHT") !=-1 or sample.find("data") !=-1 : return 1.
  else:
          print "Cross section not defined for this sample!!"
          print "--> Returning 1. for test purposes."
          return 1.

def processFile(sample, origin, target, verbose=False):

    #isSignal = True if "signal" in sample or "Zprime" in sample else False
    isSignal = True if mcType=="signal" or mcType=='bstar' else False

    if not os.path.exists(origin):
        print 'Origin directory', origin, 'does not exist, aborting...'
        sys.exit()
    if not os.path.exists(target):
        print 'Target directory', target,'does not exist, creating it now'
        os.makedirs(target)

    ## Unweighted input
    #ref_file_name = origin + '/' + sample_name
    #if not os.path.exists(ref_file_name):
    #    print '  WARNING: file', ref_file_name, 'does not exist, continuing'
    #    return True

    # first loop over all files to get nGenEvents
    totalEntries = 0.


    file_list = [origin + "/" + sample + ".root"]
    
    #file_list = []
    #j = 0

    #while True:
    #    if os.path.exists(origin + "/" + sample + "_flatTuple_{}.root".format(j)):
    #        file_list.append(origin + "/" + sample + "_flatTuple_{}.root".format(j))
    #        j += 1
    #    else:
    #        print "found {} files for sample:".format(j), sample
    #        break
    #if j == 0: 
    #    print '  WARNING: files for sample', sample , 'do not exist, continuing'
    #    return True

    if isMC:
        for infile_name in file_list:
            infile = TFile(infile_name, 'READ')
            try:
                evtHist = infile.Get('Events')
                nEvents = evtHist.GetBinContent(1)
                totalEntries += nEvents
                #print "sample:",sample,"nEvents:", nEvents
            except:
                print '  ERROR: nEvents not found in file', sample
                exit(1)
            infile.Close()
        print "totalEntries =", totalEntries

    # Cross section
    XS = getXsec(sample.replace(year+'_',''))
    print "XS = ", XS

    Leq = LUMI*XS/totalEntries if totalEntries > 0 else 0.
    #if isSignal:                                                               ## commented out since totalEntries now takes care of btagging weights in case of signal 
    #    signName = sample.replace('MC_signal_', 'ZpBB')
    #    if '2016' in signName:
    #        yr = '2016'
    #    elif '2017' in signName:
    #        yr = '2017'
    #    elif '2018' in signName:
    #        yr = '2018'
    #    signName = signName.replace(yr,'')
    #    print "number of generated events:", SAMPLE[signName]['genEvents'][yr]
    #    Leq = LUMI*XS/SAMPLE[signName]['genEvents'][yr]
    print sample, ": Leq =", (Leq if isMC else "Data")


    # Open old files now to plug in weights
    for ref_file_name in file_list:
        print "working on file:", ref_file_name

        # Weighted output
        new_file_name = ref_file_name.replace(origin, target)

        new_file = TFile(new_file_name, 'RECREATE')
        new_file.cd()

        ref_file = TFile(ref_file_name, 'READ')

        # Variables declaration
        eventWeightLumi = array('f', [1.0])# global event weight with lumi


        # get tree
        tree = ref_file.Get("tree")
        nev = tree.GetEntriesFast()
        new_file.cd()
        new_tree = tree.CopyTree("")
        # New branches
        eventWeightLumiBranch = new_tree.Branch('eventWeightLumi', eventWeightLumi, 'eventWeightLumi/F')

        # looping over events
        for event in range(0, tree.GetEntries()):
            if verbose and (event%10000==0 or event==nev-1): print ' = TTree:', tree.GetName(), 'events:', nev, '\t', int(100*float(event+1)/float(nev)), '%\r',
            tree.GetEntry(event)

            # Initialize
            eventWeightLumi[0] = 1.

            # Weights
            if isMC:
                eventWeightLumi[0] = tree.GenWeight * Leq
                if isSignal: eventWeightLumi[0] = Leq

            # Fill the branches
            eventWeightLumiBranch.Fill()
        new_file.cd()
        new_tree.Write("", TObject.kOverwrite)
        if verbose: print ' '


        # Looping over additional file content
        for key in ref_file.GetListOfKeys():
            obj = key.ReadObj()
            # Histograms
            if obj.IsA().InheritsFrom('TH1'):
                if verbose: print ' + TH1:', obj.GetName()
                new_file.cd()
                obj.Write()
            # Tree
            elif obj.IsA().InheritsFrom('TTree'):
                continue
                #nev = obj.GetEntriesFast()
                #new_file.cd()
                #new_tree = obj.CopyTree("")
                ## New branches
                #eventWeightLumiBranch = new_tree.Branch('eventWeightLumi', eventWeightLumi, 'eventWeightLumi/F')

                ## looping over events
                #for event in range(0, obj.GetEntries()):
                #    if verbose and (event%10000==0 or event==nev-1): print ' = TTree:', obj.GetName(), 'events:', nev, '\t', int(100*float(event+1)/float(nev)), '%\r',
                #    obj.GetEntry(event)
                #    # Initialize
                #    eventWeightLumi[0] = 1.
        
                #    # Weights
                #    if isMC:
                #        eventWeightLumi[0] = obj.GenWeight * Leq
                #        if isSignal: eventWeightLumi[0] = Leq

                #    # Fill the branches
                #    eventWeightLumiBranch.Fill()
                #new_file.cd()
                #new_tree.Write()
                #if verbose: print ' '

            # Directories
            elif obj.IsFolder():
                subdir = obj.GetName()
                if verbose: print ' \ Directory', subdir, ':'
                new_file.mkdir(subdir)
                new_file.cd(subdir)
                for subkey in ref_file.GetDirectory(subdir).GetListOfKeys():
                    subobj = subkey.ReadObj()
                    if subobj.IsA().InheritsFrom('TH1'):
                        if verbose: print '   + TH1:', subobj.GetName()
                        new_file.cd(subdir)
                        subobj.Write()
                new_file.cd('..')

        ref_file.Close()
        new_file.Close()

HT_bins = ['50to100', '100to200', '200to300', '300to500', '500to700', '700to1000', '1000to1500', '1500to2000', '2000toInf']
mass_bins = ['600', '800', '1000', '1200', '1400' , '1600', '1800', '2000', '2500', '3000', '3500', '4000', '4500', '5000', '5500', '6000', '7000', '8000']
mass_bins_bstar = ['500'] + [str(x) for x in range(1000,10000,1000)]
#data_2016_letters = ["B", "C", "D", "E", "F", "G", "H"]
data_2016_letters = ["B1", "B2", "C", "D", "E", "F", "G", "H"]
data_2017_letters = ["B", "C", "D", "E", "F"]
data_2018_letters = ["A", "B", "C", "D"]

#sample_name = 'test'
#sample_names = [sample_name] ## for testing

sample_names = []
if isMC:
    if mcType=="QCD":
        for HT_bin in HT_bins:  
            sample_names.append("MC_QCD_{}_HT{}".format(year, HT_bin))
    elif mcType=="signal":
        for mass_bin in mass_bins:
            sample_names.append("MC_signal_{}_M{}".format(year, mass_bin))
    elif mcType=="TTbar":
        sample_names.append("MC_TTbar_{}_TTToHadronic".format(year))
    elif mcType=='bstar':
	for mass_bin in mass_bins_bstar:
	   sample_names.append("MC_bstar_{}_M{}".format(year, mass_bin))
    else:
        print "MC typer unknown!! Aborting.."
        sys.exit()
else:
    if year=='2016':
        letters = data_2016_letters
    elif year=='2017':
        letters = data_2017_letters
    elif year=='2018':
        letters = data_2018_letters
    else:
        print "unknown year"
        sys.exit()
    for letter in letters:
        sample_names.append("data_{}_{}".format(year, letter))

jobs = []
for d in sample_names:
    #origin = global_paths.PRODUCTIONDIR+d        
    #target = global_paths.WEIGHTEDDIR+d         
    origin = global_paths.WEIGHTEDDIR[:-1]  
    target = global_paths.SKIMMEDDIR[:-1]
 
    print "working on",origin
    print "output will be stored in", target

    if singlecore:
        print " -", d
        processFile(d, origin, target, verboseout)
    else:
        p = multiprocessing.Process(target=processFile, args=(d, origin, target, verboseout,))
        jobs.append(p)
        p.start()
