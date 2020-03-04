#! /usr/bin/env python

###
### Macro for plotting the distribution of variables in the MC abckground, signal and data, as well as signal efficiency and acceptance.
###

import global_paths
import os, multiprocessing
import copy
import math
import numpy as np
from array import array
from ROOT import ROOT, gROOT, gStyle, gRandom, TSystemDirectory
from ROOT import TFile, TChain, TTree, TCut, TF1, TH1F, TH2F, THStack
from ROOT import TGraph, TGraphErrors, TGraphAsymmErrors, TVirtualFitter
from ROOT import TStyle, TCanvas, TPad
from ROOT import TLegend, TLatex, TText, TLine

from samples import sample
from variables import variable
from aliases import alias, aliasSM, working_points, dijet_bins
from aliases import additional_selections as SELECTIONS
from utils import *
import sys

########## SETTINGS ##########

import optparse
usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage)
parser.add_option("-v", "--variable", action="store", type="string", dest="variable", default="")
parser.add_option("-c", "--cut", action="store", type="string", dest="cut", default="")
parser.add_option("-y", "--year", action="store", type="string", dest="year", default="run2")
parser.add_option("-b", "--btagging", action="store", type="string", dest="btagging", default="medium")
parser.add_option("-s", "--save", action="store_true", default=False, dest="save")
parser.add_option("-n", "--norm", action="store_true", default=False, dest="norm")
parser.add_option("-B", "--blind", action="store_true", default=True, dest="blind")
parser.add_option("-f", "--final", action="store_true", default=False, dest="final")
(options, args) = parser.parse_args()

########## SETTINGS ##########

gROOT.SetBatch(True)
gStyle.SetOptStat(0)

BTAGGING    = options.btagging
NTUPLEDIR   = global_paths.SKIMMEDDIR
SIGNAL      = 1 # Signal magnification factor
RATIO       = 4 # 0: No ratio plot; !=0: ratio between the top and bottom pads
NORM        = options.norm
PARALLELIZE = False
BLIND       = False
LUMI        = {"run2" : 137190, "2016" : 35920, "2017" : 41530, "2018" : 59740}

color = {'none': 920, 'qq': 1, 'bq': 632, 'bb': 600, 'mumu': 418}
color_shift = {'none': 2, 'qq': 922, 'bq': 2, 'bb': 2, 'mumu':2}

########## SAMPLES ##########
#data = ["data_obs"]
data = []
back = ["TTbar", "QCD"]
if options.save:
    sign = ['ZpBB_M1600', 'ZpBB_M1800', 'ZpBB_M2000', 'ZpBB_M2500', 'ZpBB_M3000', 'ZpBB_M3500', 'ZpBB_M4000', 'ZpBB_M4500', 'ZpBB_M5000', 'ZpBB_M5500', 'ZpBB_M6000','ZpBB_M7000', 'ZpBB_M8000']
else:
    sign = ['ZpBB_M2000', 'ZpBB_M4000', 'ZpBB_M6000']
########## ######## ##########

if BTAGGING not in ['tight', 'medium', 'loose', 'semimedium']:
    print "unknown btagging requirement:", BTAGGING
    sys.exit()

jobs = []

def MANtag_eff(pt):
    bins = [0, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500]
    if BTAGGING=="medium":
        vals = [0.152736, 0.105698, 0.117064, 0.0904397, 0.0824952, 0.0715723, 0.0754462, 0.0843898]
    elif BTAGGING=="loose":
        vals = [0.450585, 0.407161, 0.352806, 0.321539, 0.304188, 0.295961, 0.308634, 0.285568]
    else:
        print "only medium and loose WP implemented so far"
        val = None
    for i in range(len(bins)-1):
        if pt >= bins[i] and pt < bins[i+1]: return vals[i]
    if pt>=bins[-1]: return (vals[-1]+vals[-2])*0.5
    else: print "no bin associated with pt =",pt

def MANtag_mis(pt):
    bins = [0, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500]
    if BTAGGING=="medium":
        vals = [0.0106065, 0.00855587, 0.0110678, 0.0102963, 0.00975135, 0.0109446, 0.00979731, 0.0115462]
    elif BTAGGING=="loose":
        vals = [0.096767, 0.105604, 0.0986583, 0.0967201, 0.091742, 0.105068, 0.109168, 0.0969646]
    else:
        print "only medium and loose WP implemented so far"
        val = None
    for i in range(len(bins)-1):
        if pt >= bins[i] and pt < bins[i+1]: return vals[i]
    if pt>=bins[-1]: return (vals[-1]+vals[-2])*0.5
    else: print "no bin associated with pt =",pt

def deepCSV_eff(pt):
    bins = [0, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500]
    if BTAGGING=="medium":
        vals = [0.20923, 0.172197, 0.0720872, 0.0457073, 0.0296515, 0.0169452, 0.0169157, 0.0169036]
    elif BTAGGING=="loose":
        vals = [0.669616, 0.560381, 0.438886, 0.340891, 0.269291, 0.227484, 0.20714, 0.168395]
    else:
        print "only medium and loose WP implemented so far"
        val = None
    for i in range(len(bins)-1):
        if pt >= bins[i] and pt < bins[i+1]: return vals[i]
    if pt>=bins[-1]: return (vals[-1]+vals[-2])*0.5
    else: print "no bin associated with pt =",pt

def deepCSV_mis(pt):
    bins = [0, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500]
    if BTAGGING=="medium":
        vals = [0.0103045, 0.00984539, 0.0106212, 0.00934899, 0.00953492, 0.00957432, 0.00928335, 0.00958614]
    elif BTAGGING=="loose":
        vals = [0.101894, 0.0975124, 0.105729, 0.0985992, 0.0918382, 0.0900662, 0.0948251, 0.105897]
    else:
        print "only medium and loose WP implemented so far"
        val = None
    for i in range(len(bins)-1):
        if pt >= bins[i] and pt < bins[i+1]: return vals[i]
    if pt>=bins[-1]: return (vals[-1]+vals[-2])*0.5
    else: print "no bin associated with pt =",pt


def plot(var, cut, year, norm=False, nm1=False):
    from root_numpy import root2array, fill_hist, array2root
    import numpy.lib.recfunctions as rfn
    ### Preliminary Operations ###
    treeRead = not cut in ["nnqq", "en", "enqq", "mn", "mnqq", "ee", "eeqq", "mm", "mmqq", "em", "emqq", "qqqq"] # Read from tree
    channel = cut
    unit = ''
    if "GeV" in variable[var]['title']: unit = ' GeV'
    isBlind = BLIND and 'SR' in channel
    isAH = False #'qqqq' in channel or 'hp' in channel or 'lp' in channel
    showSignal = False if 'SB' in cut or 'TR' in cut else True #'SR' in channel or channel=='qqqq'#or len(channel)==5
    stype = "HVT model B"
    if len(sign)>0 and 'AZh' in sign[0]: stype = "2HDM"
    elif len(sign)>0 and  'monoH' in sign[0]: stype = "Z'-2HDM m_{A}=300 GeV"
    if treeRead:
        for k in sorted(alias.keys(), key=len, reverse=True):
            if BTAGGING=='semimedium':
                if k in cut: 
                    cut = cut.replace(k, aliasSM[k])
        
            else:
                if k in cut: 
                    cut = cut.replace(k, alias[k].format(WP=working_points[BTAGGING]))

    
    print "Plotting from", ("tree" if treeRead else "file"), var, "in", channel, "channel with:"
    print "  cut    :", cut

    if var == 'jj_deltaEta_widejet':
        if "jj_deltaEta_widejet<1.1 && " in cut:
            print 
            print "omitting jj_deltaEta_widejet<1.1 cut to draw the deltaEta distribution"
            print
            cut = cut.replace("jj_deltaEta_widejet<1.1 && ", "")
        else:
            print
            print "no 'jj_deltaEta_widejet<1.1 && ' in the cut string detected, so it cannot be ommited explicitly"
            print
    
    ### Create and fill MC histograms ###
    # Create dict
    file = {}
    tree = {}
    hist = {}
    
    ### Create and fill MC histograms ###
    for i, s in enumerate(back+sign):
        if True: #FIXME

            if variable[var]['nbins']>0: 
                hist[s] = TH1F(s, ";"+variable[var]['title']+";Events / ( "+str((variable[var]['max']-variable[var]['min'])/variable[var]['nbins'])+unit+" );"+('log' if variable[var]['log'] else ''), variable[var]['nbins'], variable[var]['min'], variable[var]['max'])
            else: 
                hist[s] = TH1F(s, ";"+variable[var]['title']+";Events"+('log' if variable[var]['log'] else ''), len(variable[var]['bins'])-1, array('f', variable[var]['bins']))
            hist[s].Sumw2()

            for j, ss in enumerate(sample[s]['files']):
                if not 'data' in s:
                    if year=="run2" or year in ss:
                        arr = root2array(NTUPLEDIR + ss + ".root", branches=[var, "jpt_1", "jpt_2", "eventWeightLumi", "TMath::Abs(jflavour_1)==5 && TMath::Abs(jflavour_2)==5", "TMath::Abs(jflavour_1)==5 && TMath::Abs(jflavour_2)!=5", "TMath::Abs(jflavour_1)!=5 && TMath::Abs(jflavour_2)==5", "TMath::Abs(jflavour_1)!=5 && TMath::Abs(jflavour_2)!=5"], selection = cut if len(cut)>0 else "")
                        print "imported "+NTUPLEDIR + ss + ".root"
                        arr.dtype.names = [var, "jpt_1", "jpt_2", "eventWeightLumi", "bb", "bq", "qb", "qq"]
                        MANtag_eff1 = np.array(map(MANtag_eff, arr["jpt_1"]))
                        MANtag_eff2 = np.array(map(MANtag_eff, arr["jpt_2"]))
                        MANtag_mis1 = np.array(map(MANtag_mis, arr["jpt_1"]))
                        MANtag_mis2 = np.array(map(MANtag_mis, arr["jpt_2"]))
                        MANtag_weight = np.multiply(arr["eventWeightLumi"], np.multiply(arr['bb'], np.multiply(MANtag_eff1, MANtag_eff2)) + np.multiply(arr['bq'], np.multiply(MANtag_eff1, MANtag_mis2)) + np.multiply(arr['qb'], np.multiply(MANtag_mis1, MANtag_eff2)) + np.multiply(arr['qq'], np.multiply(MANtag_mis1, MANtag_mis2)) )
                        fill_hist(hist[s], arr[var], weights=MANtag_weight)
                        deepCSV_eff1 = np.array(map(deepCSV_eff, arr["jpt_1"]))
                        deepCSV_eff2 = np.array(map(deepCSV_eff, arr["jpt_2"]))
                        deepCSV_mis1 = np.array(map(deepCSV_mis, arr["jpt_1"]))
                        deepCSV_mis2 = np.array(map(deepCSV_mis, arr["jpt_2"]))
                        deepCSV_weight = np.multiply(arr["eventWeightLumi"], np.multiply(arr['bb'], np.multiply(deepCSV_eff1, deepCSV_eff2)) + np.multiply(arr['bq'], np.multiply(deepCSV_eff1, deepCSV_mis2)) + np.multiply(arr['qb'], np.multiply(deepCSV_mis1, deepCSV_eff2)) + np.multiply(arr['qq'], np.multiply(deepCSV_mis1, deepCSV_mis2)) )

                        if var == "jj_mass_widejet" and options.save and not "data" in ss:
                            arr = rfn.append_fields(arr, "MANtag_weight", MANtag_weight, usemask=False) 
                            arr = rfn.append_fields(arr, "deepCSV_weight", deepCSV_weight, usemask=False) 
                            array2root(arr, NTUPLEDIR+"MANtag/"+ss+"_"+BTAGGING+".root", treename="tree", mode='recreate')
                            print "saved as", NTUPLEDIR+"MANtag/"+ss+"_"+BTAGGING+".root"
                        arr=None

            #tree[s] = TChain("tree")
            #for j, ss in enumerate(sample[s]['files']):
            #    if not 'data' in s or ('data' in s and ss in pd):
            #        if year=="run2" or year in ss:
            #            tree[s].Add(NTUPLEDIR + ss + ".root")
            #if variable[var]['nbins']>0: hist[s] = TH1F(s, ";"+variable[var]['title']+";Events / ( "+str((variable[var]['max']-variable[var]['min'])/variable[var]['nbins'])+unit+" );"+('log' if variable[var]['log'] else ''), variable[var]['nbins'], variable[var]['min'], variable[var]['max'])
            #else: hist[s] = TH1F(s, ";"+variable[var]['title']+";Events"+('log' if variable[var]['log'] else ''), len(variable[var]['bins'])-1, array('f', variable[var]['bins']))
            #hist[s].Sumw2()
            #cutstring = "(eventWeightLumi)" + ("*("+cut+")" if len(cut)>0 else "")
            #tree[s].Project(s, var, cutstring)
            #if not tree[s].GetTree()==None: hist[s].SetOption("%s" % tree[s].GetTree().GetEntriesFast())

        #else: # Histogram written to file
        #    for j, ss in enumerate(sample[s]['files']):
        #        if not 'data' in s or ('data' in s and ss in pd):
        #            file[ss] = TFile(NTUPLEDIR + ss + ".root", "R")
        #            if file[ss].IsZombie():
        #                print "WARNING: file", NTUPLEDIR + ss + ".root", "does not exist"
        #                continue
        #            tmphist = file[ss].Get(cut+"/"+var)
        #            if tmphist==None: continue
        #            if not s in hist.keys(): hist[s] = tmphist
        #            else: hist[s].Add(tmphist)
        hist[s].Scale(sample[s]['weight'] if hist[s].Integral() >= 0 else 0)
        hist[s].SetFillColor(sample[s]['fillcolor'])
        hist[s].SetFillStyle(sample[s]['fillstyle'])
        hist[s].SetLineColor(sample[s]['linecolor'])
        hist[s].SetLineStyle(sample[s]['linestyle'])
    
    if channel.endswith('TR') and channel.replace('TR', '') in topSF:
        hist['TTbarSL'].Scale(topSF[channel.replace('TR', '')][0])
        hist['ST'].Scale(topSF[channel.replace('TR', '')][0])
    
    hist['BkgSum'] = hist['data_obs'].Clone("BkgSum") if 'data_obs' in hist else hist[back[0]].Clone("BkgSum")
    hist['BkgSum'].Reset("MICES")
    hist['BkgSum'].SetFillStyle(3003)
    hist['BkgSum'].SetFillColor(1)
    for i, s in enumerate(back): hist['BkgSum'].Add(hist[s])
    
    #if options.norm:
    #    for i, s in enumerate(back + ['BkgSum']): hist[s].Scale(hist[data[0]].Integral()/hist['BkgSum'].Integral())

    # Create data and Bkg sum histograms
    if options.blind or 'SR' in channel:
        hist['data_obs'] = hist['BkgSum'].Clone("data_obs")
        hist['data_obs'].Reset("MICES")
    # Set histogram style
    hist['data_obs'].SetMarkerStyle(20)
    hist['data_obs'].SetMarkerSize(1.25)
    
    for i, s in enumerate(back+sign+['BkgSum']): addOverflow(hist[s], False) # Add overflow
    for i, s in enumerate(sign): hist[s].SetLineWidth(3)
    for i, s in enumerate(sign): sample[s]['plot'] = True#sample[s]['plot'] and s.startswith(channel[:2])
    
    
    if isAH:
        for i, s in enumerate(back):
            hist[s].SetFillStyle(3005)
            hist[s].SetLineWidth(2)
        #for i, s in enumerate(sign):
        #    hist[s].SetFillStyle(0)
        if not var=="Events":
            sfnorm = hist[data[0]].Integral()/hist['BkgSum'].Integral()
            print "Applying SF:", sfnorm
            for i, s in enumerate(back+['BkgSum']): hist[s].Scale(sfnorm)
        if BLIND and var.endswith("Mass"):
            for i, s in enumerate(data+back+['BkgSum']):
                first, last = hist[s].FindBin(65), hist[s].FindBin(135)
                for j in range(first, last): hist[s].SetBinContent(j, -1.e-4)
        if BLIND and var.endswith("Tau21"):
            for i, s in enumerate(data):
                first, last = hist[s].FindBin(0), hist[s].FindBin(0.6)
                for j in range(first, last): hist[s].SetBinContent(j, -1.e-4)
    
    # Create stack
    if variable[var]['nbins']>0: 
        bkg = THStack("Bkg", ";"+hist['BkgSum'].GetXaxis().GetTitle()+";Events / ( "+str((variable[var]['max']-variable[var]['min'])/variable[var]['nbins'])+unit+" )")
    else: 
        bkg = THStack("Bkg", ";"+hist['BkgSum'].GetXaxis().GetTitle()+";Events; " )
    for i, s in enumerate(back): bkg.Add(hist[s])
    
    
    # Legend
    leg = TLegend(0.65, 0.6, 0.95, 0.9)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0) #1001
    leg.SetFillColor(0)
    if len(data) > 0:
        leg.AddEntry(hist[data[0]], sample[data[0]]['label'], "pe")
    for i, s in reversed(list(enumerate(['BkgSum']+back))):
        leg.AddEntry(hist[s], sample[s]['label'], "f")
    if showSignal:
        for i, s in enumerate(sign):
            if sample[s]['plot']: leg.AddEntry(hist[s], sample[s]['label'], "fl")
        
    leg.SetY1(0.9-leg.GetNRows()*0.05)
    
    
    # --- Display ---
    c1 = TCanvas("c1", hist.values()[0].GetXaxis().GetTitle(), 800, 800 if RATIO else 600)
    
    if RATIO:
        c1.Divide(1, 2)
        setTopPad(c1.GetPad(1), RATIO)
        setBotPad(c1.GetPad(2), RATIO)
    c1.cd(1)
    c1.GetPad(bool(RATIO)).SetTopMargin(0.06)
    c1.GetPad(bool(RATIO)).SetRightMargin(0.05)
    c1.GetPad(bool(RATIO)).SetTicks(1, 1)
    
    log = variable[var]['log'] #"log" in hist['BkgSum'].GetZaxis().GetTitle()
    if log: c1.GetPad(bool(RATIO)).SetLogy()
        
    # Draw
    bkg.Draw("HIST") # stack
    hist['BkgSum'].Draw("SAME, E2") # sum of bkg
    if not isBlind and len(data) > 0: hist['data_obs'].Draw("SAME, PE") # data
    if 'sync' in hist: hist['sync'].Draw("SAME, PE")
    #data_graph.Draw("SAME, PE")
    if showSignal:
        smagn = 1. #if treeRead else 1.e2 #if log else 1.e2
        for i, s in enumerate(sign):
    #        if sample[s]['plot']:
                hist[s].Scale(smagn)
                hist[s].Draw("SAME, HIST") # signals Normalized, hist[s].Integral()*sample[s]['weight']
        textS = drawText(0.80, 0.9-leg.GetNRows()*0.05 - 0.02, stype+" (x%d)" % smagn, True)
    #bkg.GetYaxis().SetTitleOffset(bkg.GetYaxis().GetTitleOffset()*1.075)
    bkg.GetYaxis().SetTitleOffset(0.9)
    #bkg.GetYaxis().SetTitleOffset(2.)
    bkg.SetMaximum((5. if log else 1.25)*max(bkg.GetMaximum(), hist['data_obs'].GetBinContent(hist['data_obs'].GetMaximumBin())+hist['data_obs'].GetBinError(hist['data_obs'].GetMaximumBin())))
    #if bkg.GetMaximum() < max(hist[sign[0]].GetMaximum(), hist[sign[-1]].GetMaximum()): bkg.SetMaximum(max(hist[sign[0]].GetMaximum(), hist[sign[-1]].GetMaximum())*1.25)
    bkg.SetMinimum(max(min(hist['BkgSum'].GetBinContent(hist['BkgSum'].GetMinimumBin()), hist['data_obs'].GetMinimum()), 5.e-1)  if log else 0.)
    if log:
        bkg.GetYaxis().SetNoExponent(bkg.GetMaximum() < 1.e4)
        #bkg.GetYaxis().SetMoreLogLabels(True)
    bkg.GetXaxis().SetRangeUser(variable[var]['min'], variable[var]['max'])  
 
    #if log: bkg.SetMinimum(1)
    leg.Draw()
    #drawCMS(LUMI[year], "Preliminary")
    drawCMS(LUMI[year], "Work in Progress", suppressCMS=True)
    drawRegion('XVH'+channel, True)
    drawAnalysis(channel)
    
    setHistStyle(bkg, 1.2 if RATIO else 1.1)
    setHistStyle(hist['BkgSum'], 1.2 if RATIO else 1.1)
       
    if RATIO:
        c1.cd(2)
        err = hist['BkgSum'].Clone("BkgErr;")
        err.SetTitle("")
        err.GetYaxis().SetTitle("Data / MC")
        err.GetYaxis().SetTitleOffset(0.9)
 
        err.GetXaxis().SetRangeUser(variable[var]['min'], variable[var]['max'])  
        for i in range(1, err.GetNbinsX()+1):
            err.SetBinContent(i, 1)
            if hist['BkgSum'].GetBinContent(i) > 0:
                err.SetBinError(i, hist['BkgSum'].GetBinError(i)/hist['BkgSum'].GetBinContent(i))
        setBotStyle(err)
        errLine = err.Clone("errLine")
        errLine.SetLineWidth(1)
        errLine.SetFillStyle(0)
        res = hist['data_obs'].Clone("Residues")
        for i in range(0, res.GetNbinsX()+1):
            if hist['BkgSum'].GetBinContent(i) > 0: 
                res.SetBinContent(i, res.GetBinContent(i)/hist['BkgSum'].GetBinContent(i))
                res.SetBinError(i, res.GetBinError(i)/hist['BkgSum'].GetBinContent(i))
        if 'sync' in hist:
            res.SetMarkerColor(2)
            res.SetMarkerStyle(31)
            res.Reset()
            for i in range(0, res.GetNbinsX()+1):
                x = hist['data_obs'].GetXaxis().GetBinCenter(i)
                if hist['sync'].GetBinContent(hist['sync'].FindBin(x)) > 0: 
                    res.SetBinContent(i, hist['data_obs'].GetBinContent(hist['data_obs'].FindBin(x))/hist['sync'].GetBinContent(hist['sync'].FindBin(x)))
                    res.SetBinError(i, hist['data_obs'].GetBinError(hist['data_obs'].FindBin(x))/hist['sync'].GetBinContent(hist['sync'].FindBin(x)))
        setBotStyle(res)
        #err.GetXaxis().SetLabelOffset(err.GetXaxis().GetLabelOffset()*5)
        #err.GetXaxis().SetTitleOffset(err.GetXaxis().GetTitleOffset()*2)
        err.Draw("E2")
        errLine.Draw("SAME, HIST")
        if not isBlind and len(data) > 0:
            res.Draw("SAME, PE0")
            #res_graph.Draw("SAME, PE0")
            if len(err.GetXaxis().GetBinLabel(1))==0: # Bin labels: not a ordinary plot
                drawRatio(hist['data_obs'], hist['BkgSum'])
                drawStat(hist['data_obs'], hist['BkgSum'])

    c1.Update()

    if gROOT.IsBatch():
        if channel=="": channel="nocut"
        varname = var.replace('.', '_').replace('()', '')
        if not os.path.exists("plots/"+channel): os.makedirs("plots/"+channel)
        suffix = ''
        if "b" in channel or 'mu' in channel: suffix+="_"+BTAGGING
        c1.Print("plots/MANtag_study/"+channel+"/"+varname+"_"+year+suffix+".png")
        c1.Print("plots/MANtag_study/"+channel+"/"+varname+"_"+year+suffix+".pdf")
    
    # Print table
    printTable(hist, sign)
    
#    if True:
#        sFile = TFile("sync/data_2016.root", "RECREATE")
#        sFile.cd()
#        hist['data_obs'].
        
    
    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")

    
########## ######## ##########

plot(options.variable, options.cut, options.year)

