#! /usr/bin/env python

###
### Macro for plotting the distribution of variables in the MC abckground, signal and data, as well as signal efficiency and acceptance.
###

import global_paths
import os, multiprocessing
import copy
import math
from array import array
from ROOT import ROOT, gROOT, gStyle, gRandom, TSystemDirectory
from ROOT import TFile, TChain, TTree, TCut, TF1, TH1F, TH2F, THStack
from ROOT import TGraph, TGraphErrors, TGraphAsymmErrors, TVirtualFitter, TMultiGraph
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
parser.add_option("-n", "--norm", action="store_true", default=False, dest="norm")
parser.add_option("-B", "--blind", action="store_true", default=False, dest="blind")
parser.add_option("-f", "--final", action="store_true", default=False, dest="final")
parser.add_option("-e", "--efficiency", action="store_true", default=False, dest="efficiency")
parser.add_option("-s", "--selection", action="store", type="string", dest="selection", default="")
parser.add_option("-a", "--acceptance", action="store_true", default=False, dest="acceptance")
parser.add_option("-t", "--trigger", action="store_true", default=False, dest="trigger")
parser.add_option("", "--separate", action="store_true", default=False, dest="separate")
parser.add_option("", "--btagging_eff", action="store_true", default=False, dest="btagging_eff")
parser.add_option("", "--sync", action="store_true", default=False, dest="sync")
(options, args) = parser.parse_args()

########## SETTINGS ##########

gROOT.SetBatch(True)
gStyle.SetOptStat(0)

BTAGGING    = options.btagging
NTUPLEDIR   = global_paths.SKIMMEDDIR
ACCEPTANCEDIR = "acceptance/"
TRIGGERDIR = global_paths.SKIMMEDDIR+"TriggerStudy"
SIGNAL      = 1 # Signal magnification factor
RATIO       = 4 # 0: No ratio plot; !=0: ratio between the top and bottom pads
if options.blind: RATIO = 0
NORM        = options.norm
PARALLELIZE = False
BLIND       = False
LUMI        = {"run2" : 137190, "2016" : 35920, "2017" : 41530, "2018" : 59740}
ADDSELECTION= options.selection!=""
SYNC        = options.sync
BTAGGEFFVARS= ["jCSV", "jdeepCSV", "jdeepFlavour"]
SEPARATE    = options.separate

color = {'none': 920, 'qq': 1, 'bq': 632, 'bb': 600, 'mumu': 418}
color_shift = {'none': 2, 'qq': 922, 'bq': 2, 'bb': 2, 'mumu':2}
if options.selection not in SELECTIONS.keys():
    print "invalid selection!"
    sys.exit()
btag_colors = {"jdeepFlavour":801, "jdeepCSV":6, "jCSV":4}
btag_titles = {"jCSV": "CSVv2", "jdeepCSV": "DeepCSV", "jdeepFlavour": "DeepJet"}

########## SAMPLES ##########
data = ["data_obs"]
back = ["TTbar", "QCD"]
sign = ['ZpBB_M2000', 'ZpBB_M4000', 'ZpBB_M6000']#, 'ZpBB_M8000']
########## ######## ##########

if BTAGGING not in ['tight', 'medium', 'loose', 'semimedium']:
    print "unknown btagging requirement:", BTAGGING
    sys.exit()

jobs = []

def plot(var, cut, year, norm=False, nm1=False):
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
                    if ADDSELECTION:
                        cut = cut.replace(k, aliasSM[k]+SELECTIONS[options.selection])
                    else:
                        cut = cut.replace(k, aliasSM[k])
        
            else:
                if k in cut: 
                    if ADDSELECTION:
                        cut = cut.replace(k, alias[k].format(WP=working_points[BTAGGING])+SELECTIONS[options.selection])
                    else:
                        cut = cut.replace(k, alias[k].format(WP=working_points[BTAGGING]))

    
    # Determine Primary Dataset
    pd = sample['data_obs']['files']
    
    print "Plotting from", ("tree" if treeRead else "file"), var, "in", channel, "channel with:"
    print "  dataset:", pd
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
    for i, s in enumerate(data+back+sign):
        if treeRead: # Project from tree
            tree[s] = TChain("tree")
            for j, ss in enumerate(sample[s]['files']):
                if not 'data' in s or ('data' in s and ss in pd):
                    if year=="run2" or year in ss:
                        tree[s].Add(NTUPLEDIR + ss + ".root")
            if variable[var]['nbins']>0: hist[s] = TH1F(s, ";"+variable[var]['title']+";Events / ( "+str((variable[var]['max']-variable[var]['min'])/variable[var]['nbins'])+unit+" );"+('log' if variable[var]['log'] else ''), variable[var]['nbins'], variable[var]['min'], variable[var]['max'])
            else: hist[s] = TH1F(s, ";"+variable[var]['title']+";Events"+('log' if variable[var]['log'] else ''), len(variable[var]['bins'])-1, array('f', variable[var]['bins']))
            hist[s].Sumw2()
            cutstring = "(eventWeightLumi)" + ("*("+cut+")" if len(cut)>0 else "")
            tree[s].Project(s, var, cutstring)
            if not tree[s].GetTree()==None: hist[s].SetOption("%s" % tree[s].GetTree().GetEntriesFast())
        else: # Histogram written to file
            for j, ss in enumerate(sample[s]['files']):
                if not 'data' in s or ('data' in s and ss in pd):
                    file[ss] = TFile(NTUPLEDIR + ss + ".root", "R")
                    if file[ss].IsZombie():
                        print "WARNING: file", NTUPLEDIR + ss + ".root", "does not exist"
                        continue
                    tmphist = file[ss].Get(cut+"/"+var)
                    if tmphist==None: continue
                    if not s in hist.keys(): hist[s] = tmphist
                    else: hist[s].Add(tmphist)
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
    
    if options.norm:
        for i, s in enumerate(back + ['BkgSum']): hist[s].Scale(hist[data[0]].Integral()/hist['BkgSum'].Integral())

    # Create data and Bkg sum histograms
    if options.blind or 'SR' in channel:
        hist['data_obs'] = hist['BkgSum'].Clone("data_obs")
        hist['data_obs'].Reset("MICES")
    # Set histogram style
    hist['data_obs'].SetMarkerStyle(20)
    hist['data_obs'].SetMarkerSize(1.25)
    
    for i, s in enumerate(data+back+sign+['BkgSum']): addOverflow(hist[s], False) # Add overflow
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
    
    if SYNC and var == "jj_mass_widejet" and year in ["2016", "2017", "2018"]:
        #iFile = TFile("sync/JetHT_run" + year + "_red_cert_scan.root", "READ")
        #hist['sync'] = iFile.Get("Mjj")
        if year == '2016':
            iFile = TFile("sync/2016/2016_07Aug2017_1246_1p1.root", "READ")
            hist['sync'] = iFile.Get("h_mjj_data")
        elif year == '2017':
            iFile = TFile("sync/2017/histos_Run2017BCDEF_17Nov2017_JEC2017_mjj1530_cemf_lt_0p8_deltaETA_lt_1p1.root", "READ")
            hist['sync'] = iFile.Get("h_mjj_data")
        elif year == '2018':
            iFile = TFile("sync/2018/Double_sideband_inputs_18v10_preliminary_v2.root", "READ")
            hist['sync'] = iFile.Get("h_mjj")
   
#        hist['sync'] = tmp.Rebin(len(dijet_bins)-1, "sync", array('d', dijet_bins))
#        hist['sync'] = tmp.Rebin(100, "sync")
        hist['sync'].SetMarkerStyle(31)
        hist['sync'].SetMarkerSize(1.25)
        hist['sync'].SetMarkerColor(2)
        print "Imported and drawing sync file"
    
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
    #drawCMS(LUMI[year], "Work in Progress", suppressCMS=True)
    drawCMS(LUMI[year], "", suppressCMS=True)
    drawRegion('XVH'+channel, True)
    drawAnalysis(channel)
    
    setHistStyle(bkg, 1.2 if RATIO else 1.1)
    setHistStyle(hist['BkgSum'], 1.2 if RATIO else 1.1)
       
    if RATIO:
        c1.cd(2)
        err = hist['BkgSum'].Clone("BkgErr;")
        err.SetTitle("")
        if SYNC:
            err.GetYaxis().SetTitle("Nano/Mini")
        else:
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
            res.SetMarkerColor(1)
            res.SetMarkerStyle(20)
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
        if SYNC: err.GetYaxis().SetRangeUser(0.9,1.1)

    c1.Update()

    if gROOT.IsBatch():
        if channel=="": channel="nocut"
        varname = var.replace('.', '_').replace('()', '')
        if not os.path.exists("plots/"+channel): os.makedirs("plots/"+channel)
        suffix = ''
        if "b" in channel or 'mu' in channel: suffix+="_"+BTAGGING
        if ADDSELECTION: suffix+="_"+options.selection
        c1.Print("plots/"+channel+"/"+varname+"_"+year+suffix+".png")
        c1.Print("plots/"+channel+"/"+varname+"_"+year+suffix+".pdf")
    
    # Print table
    printTable(hist, sign)
    
#    if True:
#        sFile = TFile("sync/data_2016.root", "RECREATE")
#        sFile.cd()
#        hist['data_obs'].
        
    
    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")

    
########## ######## ##########


def efficiency(year):
    import numpy as np
    from root_numpy import tree2array, fill_hist
    from aliases import AK8veto, electronVeto, muonVeto
    genPoints = [1800, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000, 8000]
    eff = {}
    vetoes = {"AK8":AK8veto, "electron": electronVeto, "muon": muonVeto}
    VETO = "AK8" ##could change the veto to investigate here
    if SEPARATE: eff_add = {}
    
    #channels = ['none', 'qq', 'bq', 'bb', 'mumu']
    channels = ['qq', 'bq', 'bb', 'mumu']

    for channel in channels:
        treeSign = {}
        ngenSign = {}
        nevtSign = {}
        eff[channel] = TGraphErrors()
        if SEPARATE:
            nevtSign_add = {}
            eff_add[channel] = TGraphErrors()

        for i, m in enumerate(genPoints):
            signName = "ZpBB_M"+str(m)
            ngenSign[m] = 0.
            nevtSign[m] = 0.
            if SEPARATE: nevtSign_add[m] = 0.
            for j, ss in enumerate(sample[signName]['files']):
                if year=="run2" or year in ss:
                    sfile = TFile(NTUPLEDIR + ss + ".root", "READ")
                    ngenSign[m] += sfile.Get("Events").GetBinContent(1) 
                    treeSign[m] = sfile.Get("tree")
                    if BTAGGING=='semimedium':
                        #if SEPARATE:
                        #    temp_array = tree2array(treeSign[m], branches='BTagAK4Weight_deepJet', selection=aliasSM[channel].replace(vetoes[VETO], ""))
                        #else:
                        temp_array = tree2array(treeSign[m], branches='BTagAK4Weight_deepJet', selection=aliasSM[channel]) 
                        temp_hist = TH1F('pass', 'pass', 1,0,1)                                     
                        fill_hist(temp_hist, np.zeros(len(temp_array)), weights=temp_array)         
                        nevtSign[m] += temp_hist.GetBinContent(1)                                   
                        temp_array=None; temp_hist.Reset()                                          
                        if SEPARATE: 
                            temp_array = tree2array(treeSign[m], branches='BTagAK4Weight_deepJet', selection=aliasSM[channel].replace(vetoes[VETO], "")) 
                            temp_hist = TH1F('pass', 'pass', 1,0,1)                                     
                            fill_hist(temp_hist, np.zeros(len(temp_array)), weights=temp_array)         
                            nevtSign[m] += temp_hist.GetBinContent(1)                                   
                            temp_array=None; temp_hist.Reset()                                          
                    else:
                        #if SEPARATE:
                        #    temp_array = tree2array(treeSign[m], branches='BTagAK4Weight_deepJet', selection=alias[channel].format(WP=working_points[BTAGGING]).replace(vetoes[VETO], ""))               
                        #else:
                        temp_array = tree2array(treeSign[m], branches='BTagAK4Weight_deepJet', selection=alias[channel].format(WP=working_points[BTAGGING]))
                        temp_hist = TH1F('pass', 'pass', 1,0,1)                                     
                        fill_hist(temp_hist, np.zeros(len(temp_array)), weights=temp_array)         
                        nevtSign[m] += temp_hist.GetBinContent(1)                                   
                        temp_array=None; temp_hist.Reset()                                          
                        if SEPARATE: 
                            temp_array = tree2array(treeSign[m], branches='BTagAK4Weight_deepJet', selection=alias[channel].format(WP=working_points[BTAGGING]).replace(vetoes[VETO], ""))
                            temp_hist = TH1F('pass', 'pass', 1,0,1)                                     
                            fill_hist(temp_hist, np.zeros(len(temp_array)), weights=temp_array)         
                            nevtSign_add[m] += temp_hist.GetBinContent(1)                                   
                            temp_array=None; temp_hist.Reset()                                          

                    sfile.Close()
                    print channel, ss, ":", nevtSign[m], "/", ngenSign[m], "=", nevtSign[m]/ngenSign[m]
            if nevtSign[m] == 0 or ngenSign[m] < 0: continue
            n = eff[channel].GetN()
            eff[channel].SetPoint(n, m, nevtSign[m]/ngenSign[m])
            eff[channel].SetPointError(n, 0, math.sqrt(nevtSign[m])/ngenSign[m])
            if SEPARATE:
                eff_add[channel].SetPoint(n, m, nevtSign_add[m]/ngenSign[m])
                eff_add[channel].SetPointError(n, 0, math.sqrt(nevtSign_add[m])/ngenSign[m])

        eff[channel].SetMarkerColor(color[channel])
        eff[channel].SetMarkerStyle(20)
        eff[channel].SetLineColor(color[channel])
        eff[channel].SetLineWidth(2)

        if SEPARATE:
            eff_add[channel].SetMarkerColor(color[channel]+color_shift[channel])
            eff_add[channel].SetMarkerStyle(21)
            eff_add[channel].SetLineColor(color[channel]+color_shift[channel])
            eff_add[channel].SetLineWidth(2)
            eff_add[channel].SetLineStyle(7)

        if channel=='qq' or channel=='none': eff[channel].SetLineStyle(3)

    n = max([eff[x].GetN() for x in channels])
    maxEff = 0.

    # Total efficiency
    eff["sum"] = TGraphErrors(n)
    eff["sum"].SetMarkerStyle(24)
    eff["sum"].SetMarkerColor(1)
    eff["sum"].SetLineWidth(2)
    
    if SEPARATE:
        eff_add["sum"] = TGraphErrors(n)
        eff_add["sum"].SetMarkerStyle(25)
        eff_add["sum"].SetMarkerColor(1)
        eff_add["sum"].SetLineWidth(2)
        eff_add["sum"].SetLineStyle(7)

    for i in range(n):
        tot, mass = 0., 0.
        if SEPARATE: tot_add = 0.
        for channel in channels:
            if channel=='qq' or channel=='none': continue #not sure if I should include 2mu category in sum
            if eff[channel].GetN() > i:
                tot += eff[channel].GetY()[i]
                if SEPARATE: tot_add += eff_add[channel].GetY()[i]
                mass = eff[channel].GetX()[i]
                if tot > maxEff: maxEff = tot
        eff["sum"].SetPoint(i, mass, tot)
        if SEPARATE: eff_add["sum"].SetPoint(i, mass, tot_add)


    if SEPARATE:
        leg = TLegend(0.15, 0.50, 0.95, 0.8)
    else:
        leg = TLegend(0.15, 0.60, 0.95, 0.8)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0) #1001
    leg.SetFillColor(0)
    leg.SetNColumns(len(channels)/4)
    for i, channel in enumerate(channels):
        if eff[channel].GetN() > 0: 
            leg.AddEntry(eff[channel], getChannel(channel), "pl")
            if SEPARATE: leg.AddEntry(eff_add[channel], getChannel(channel)+" no "+VETO+"-veto", "pl") 
    if SEPARATE: 
        leg.SetY1(leg.GetY2()-len([x for x in channels if eff[x].GetN() > 0])*0.045)
    else:
        leg.SetY1(leg.GetY2()-len([x for x in channels if eff[x].GetN() > 0])/2.*0.045)
    if SEPARATE:
        legS = TLegend(0.5, 0.8-0.045, 0.9, 0.85)
    else:
        legS = TLegend(0.5, 0.85-0.045, 0.9, 0.85)
    legS.SetBorderSize(0)
    legS.SetFillStyle(0) #1001
    legS.SetFillColor(0)
    legS.AddEntry(eff['sum'], "Total b tag efficiency (1 b tag + 2 b tag + 2 #mu)", "pl")
    if SEPARATE: legS.AddEntry(eff_add['sum'], "Total b tag efficiency, no "+VETO+"-veto", "pl")
    c1 = TCanvas("c1", "Signal Efficiency", 1200, 800)
    c1.cd(1)
    eff['sum'].Draw("APL")
    if SEPARATE: eff_add['sum'].Draw("SAME, PL")
    for i, channel in enumerate(channels): 
        eff[channel].Draw("SAME, PL")
        if SEPARATE: eff_add[channel].Draw("SAME, PL")
    leg.Draw()
    legS.Draw()
    setHistStyle(eff["sum"], 1.1)
    eff["sum"].SetTitle(";m_{Z'} (GeV);Acceptance #times efficiency")
    eff["sum"].SetMinimum(0.)
    eff["sum"].SetMaximum(max(1., maxEff*1.5)) #0.65
    if SEPARATE: 
        eff_add["sum"].SetTitle(";m_{Z'} (GeV);Acceptance #times efficiency")
        eff_add["sum"].SetMinimum(0.)
        eff_add["sum"].SetMaximum(1.)

    eff["sum"].GetXaxis().SetTitleSize(0.045)
    eff["sum"].GetYaxis().SetTitleSize(0.045)
    eff["sum"].GetYaxis().SetTitleOffset(1.1)
    eff["sum"].GetXaxis().SetTitleOffset(1.05)
    eff["sum"].GetXaxis().SetRangeUser(1500, 8000)
    c1.SetTopMargin(0.05)
    #drawCMS(-1, "Simulation Preliminary", year=year) #Preliminary
    #drawCMS(-1, "Work in Progress", year=year, suppressCMS=True)
    drawCMS(-1, "", year=year, suppressCMS=True)
    drawAnalysis("")

    if SEPARATE:
        c1.Print("plots/Efficiency/"+year+"_"+BTAGGING+"_no"+VETO+"veto.pdf") 
        c1.Print("plots/Efficiency/"+year+"_"+BTAGGING+"_no"+VETO+"veto.png") 
    else:
        c1.Print("plots/Efficiency/"+year+"_"+BTAGGING+".pdf") 
        c1.Print("plots/Efficiency/"+year+"_"+BTAGGING+".png") 

    # print
    print "category",
    for m in range(0, eff["sum"].GetN()):
        print " & %d" % int(eff["sum"].GetX()[m]),
    print "\\\\", "\n\\hline"
    for i, channel in enumerate(channels+["sum"]):
        if channel=='sum': print "\\hline"
        print getChannel(channel).replace("high ", "H").replace("low ", "L").replace("purity", "P").replace("b-tag", ""),
        for m in range(0, eff[channel].GetN()):
            print "& %.1f" % (100.*eff[channel].GetY()[m]),
        print "\\\\"


def acceptance(year):
    genPoints = [1800, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000, 8000]
    
    treeSign = {}
    ngenSign = {}
    nevtSign = {}
    nevtSign_eta = {}
    nevtSign_dEta = {}
    eff = TGraphErrors()
    eff_eta = TGraphErrors()
    eff_dEta = TGraphErrors()

    for i, m in enumerate(genPoints):
        ngenSign[m] = 0.
        nevtSign[m] = 0.
        nevtSign_eta[m] = 0.
        nevtSign_dEta[m] = 0.

        if year == "run2":
            years = ['2016', '2017', '2018']
        else:
            years = [year]

        for yr in years: 
            signName = "MC_signal_{}_M{}".format(yr, m)
            sfile = TFile(ACCEPTANCEDIR + signName + "_acceptanceHist.root", "READ")

            ngenSign[m] += sample["ZpBB_M"+str(m)]['genEvents'][yr]

            #all_events_hist = sfile.Get('all_events')
            #nEvents = all_events_hist.GetBinContent(1)
            #ngenSign[m] += nEvents  
            
            passing_events_hist = sfile.Get('passing')
            eta_flag_hist = sfile.Get('eta_flag')
            dEta_flag_hist = sfile.Get('dEta_flag')
            
            nEvents = passing_events_hist.GetBinContent(1)
            nEvents_eta = eta_flag_hist.GetBinContent(1)
            nEvents_dEta = dEta_flag_hist.GetBinContent(1)

            nevtSign[m] += nEvents
            nevtSign_eta[m] += nEvents_eta
            nevtSign_dEta[m] += nEvents_dEta

            sfile.Close()
        
        print m, ":", nevtSign[m], "/", ngenSign[m], "=", nevtSign[m]/ngenSign[m]
        if nevtSign[m] == 0 or ngenSign[m] < 0: continue
        n = eff.GetN()
        eff.SetPoint(n, m, nevtSign[m]/ngenSign[m])
        eff.SetPointError(n, 0, math.sqrt(nevtSign[m])/ngenSign[m])
        eff_eta.SetPoint(n, m, nevtSign_eta[m]/ngenSign[m])
        eff_eta.SetPointError(n, 0, math.sqrt(nevtSign_eta[m])/ngenSign[m])
        eff_dEta.SetPoint(n, m, nevtSign_dEta[m]/ngenSign[m])
        eff_dEta.SetPointError(n, 0, math.sqrt(nevtSign_dEta[m])/ngenSign[m])

    eff.SetMarkerColor(4)
    eff.SetMarkerStyle(24)
    eff.SetMarkerSize(2)
    eff.SetLineColor(4)
    eff.SetLineWidth(3)
    eff_eta.SetMarkerColor(2)
    eff_eta.SetMarkerStyle(23)
    eff_eta.SetMarkerSize(2)
    eff_eta.SetLineColor(2)
    eff_eta.SetLineWidth(2)
    eff_eta.SetLineStyle(2)
    eff_dEta.SetMarkerColor(418)
    eff_dEta.SetMarkerStyle(23)
    eff_dEta.SetMarkerSize(2)
    eff_dEta.SetLineColor(418)
    eff_dEta.SetLineWidth(2)
    eff_dEta.SetLineStyle(2)

    n = eff.GetN()
    maxEff = 0.

    leg = TLegend(0.15, 0.7, 0.95, 0.8)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0) #1001
    leg.SetFillColor(0)
    #leg.SetY1(leg.GetY2()-len([x for x in channels if eff[x].GetN() > 0])/2.*0.045)

    leg.AddEntry(eff, "total") 
    leg.AddEntry(eff_eta, "|#eta|<2.5")
    leg.AddEntry(eff_dEta, "#Delta#eta<1.1")

    #legS = TLegend(0.5, 0.85-0.045, 0.9, 0.85)
    #legS.SetBorderSize(0)
    #legS.SetFillStyle(0) #1001
    #legS.SetFillColor(0)
    #legS.AddEntry(eff['sum'], "Total efficiency (1 b tag + 2 b tag)", "pl")

    c1 = TCanvas("c1", "Signal Acceptance", 1200, 800)
    c1.cd(1)
    eff.Draw("APL")
    eff_eta.Draw("SAME, PL")
    eff_dEta.Draw("SAME, PL")
    leg.Draw()
    #legS.Draw()
    #setHistStyle(eff["sum"], 1.1)
    eff.SetTitle(";m_{Z'} (GeV);Acceptance")
    eff.SetMinimum(0.)
    eff.SetMaximum(max(1.5, maxEff*1.5)) #0.65

    eff.GetXaxis().SetTitleSize(0.045)
    eff.GetYaxis().SetTitleSize(0.045)
    eff.GetYaxis().SetTitleOffset(1.1)
    eff.GetXaxis().SetTitleOffset(1.05)
    eff.GetXaxis().SetRangeUser(1500, 8000)
    c1.SetTopMargin(0.05)
    #drawCMS(-1, "Simulation Preliminary", year=year) #Preliminary
    #drawCMS(-1, "Work in Progress", year=year, suppressCMS=True)
    drawCMS(-1, "", year=year, suppressCMS=True)
    drawAnalysis("")

    c1.Print("plots/Efficiency/"+year+"_Acceptance.pdf") 
    c1.Print("plots/Efficiency/"+year+"_Acceptance.png") 


def trigger_efficiency(year, separate=False): 
    from root_numpy import root2array, fill_hist
    from aliases import triggers, triggers_PFHT, triggers_Jet, triggers_BTag 
    import numpy as np
    #spec_triggers = {"PFHT": triggers_PFHT, "Jet": triggers_Jet, "BTag": triggers_BTag}
    spec_triggers = {"HT/Jet": "("+triggers_PFHT+" || "+triggers_Jet+")", "BTag": triggers_BTag}
    spec_triggers_colors = {"PFHT": 418, "Jet": 4, "BTag": 6, "HT/Jet": 4, "total": 2}

    hist_pass = TH1F("pass", "pass", 100, 0., 10000.)
    if separate:
        hist_pass_spec = {}
        for trig in spec_triggers.keys(): hist_pass_spec[trig] = TH1F("pass_"+trig, "pass_"+trig, 100, 0., 10000.)
    hist_all = TH1F("all", "all", 100, 0., 10000.)

    file_list = []

    data_2016_letters = ["B", "C", "D", "E", "F", "G", "H"]
    data_2017_letters = ["B", "C", "D", "E", "F"]
    data_2018_letters = ["A", "B", "C", "D"]
    
    sample_names = []
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
        #dir_content =  os.listdir(TRIGGERDIR+"/SingleMuon_{}_{}/".format(year, letter)) ## intended to run directly on ntuples
        #for entry in dir_content:
        #    if "_flatTuple" in entry: file_list.append(TRIGGERDIR+"/SingleMuon_{}_{}/".format(year, letter)+entry)
        file_list.append(TRIGGERDIR+"/SingleMuon_{}_{}.root".format(year, letter))
        print "appending:",TRIGGERDIR+"/SingleMuon_{}_{}.root".format(year, letter)
    
    for file_name in file_list:
        temp_array = root2array(file_name, treename='tree', branches='jj_mass_widejet', selection="jj_deltaEta_widejet<1.1")
        fill_hist(hist_all, temp_array)
        temp_array = root2array(file_name, treename='tree', branches='jj_mass_widejet', selection="jj_deltaEta_widejet<1.1 && "+triggers)
        fill_hist(hist_pass, temp_array)
        if separate:
            for trig in spec_triggers.keys():
                temp_array = root2array(file_name, treename='tree', branches='jj_mass_widejet', selection="jj_deltaEta_widejet<1.1 && "+spec_triggers[trig])
                fill_hist(hist_pass_spec[trig], temp_array)
        temp_array=None

    import array
    from aliases import dijet_bins 
    binning=[]
    for num in dijet_bins:
        if num<=10000: binning.append(num)
    #binning = range(0,1500,100)+range(1500,2000,100)+range(2000,3100,150)+range(3100,10000,300)
    binning_ = array.array('d', binning)
    hist_pass2 = hist_pass.Rebin(len(binning_)-1, "hist_pass_rebinned", binning_)
    hist_all2 = hist_all.Rebin(len(binning_)-1, "hist_all_rebinned", binning_)

    if separate:
        hist_pass_spec2 = {}
        for trig in spec_triggers.keys():
            hist_pass_spec2[trig] = hist_pass_spec[trig].Rebin(len(binning_)-1, "hist_pass_"+trig+"_rebinned", binning_)      
   
    hist_pass2.Sumw2()
    hist_all2.Sumw2()        
    eff = TGraphAsymmErrors()
    eff.Divide(hist_pass2, hist_all2)

    eff.SetMarkerColor(spec_triggers_colors["total"])
    if separate:
        eff.SetMarkerStyle(5)
    else:
        eff.SetMarkerStyle(1)
    eff.SetLineColor(spec_triggers_colors["total"])
    eff.SetLineWidth(2)

    if separate:
        eff_spec = {}
        for trig in spec_triggers.keys():
            hist_pass_spec2[trig].Sumw2()
            eff_spec[trig] = TGraphAsymmErrors()
            eff_spec[trig].Divide(hist_pass_spec2[trig], hist_all2)
            eff_spec[trig].SetMarkerColor(spec_triggers_colors[trig])
            eff_spec[trig].SetMarkerStyle(1)
            eff_spec[trig].SetLineColor(spec_triggers_colors[trig])
            eff_spec[trig].SetLineWidth(2)
       
    one_line = TGraph()
    one_line.SetPoint(0, 0., 1.)
    one_line.SetPoint(1, 10000., 1.)
    one_line.SetLineStyle(2)

    c1 = TCanvas("c1", "Trigger Efficiency", 800, 800)
    c1.cd(1)
    eff.Draw("AP")
    one_line.Draw("L")
    eff.SetTitle(";m_{jj} (GeV);trigger efficiency")
    eff.SetMinimum(0.)
    eff.SetMaximum(1.4) #0.65

    ## new
    dijet_bin_centers = []
    for b, lthr in enumerate(dijet_bins[:-1]):
        if lthr<1200 or lthr > 2500: continue
        dijet_bin_centers.append(0.5*(dijet_bins[b]+dijet_bins[b+1]))
    print "total trigger efficiency:"
    for cval in dijet_bin_centers:
         print cval,":", eff.Eval(cval)
    ## end new

    if separate:
        leg = TLegend(0.65,0.75, 0.9, 0.95)
        leg.AddEntry(eff, "total")
        for trig in spec_triggers.keys():
            leg.AddEntry(eff_spec[trig], trig+"-based")
            eff_spec[trig].Draw("P SAME")
            ## new
            print trig, "trigger efficiency"
            for cval in dijet_bin_centers:
                print cval,":", eff_spec[trig].Eval(cval)
            ## end new
        leg.Draw()

    eff.GetXaxis().SetTitleSize(0.045)
    eff.GetYaxis().SetTitleSize(0.045)
    eff.GetYaxis().SetTitleOffset(1.1)
    eff.GetXaxis().SetTitleOffset(1.05)
    eff.GetXaxis().SetLimits(700., 5000.)
    c1.SetTopMargin(0.05)
    #drawCMS(-1, "Preliminary", year=year) #Preliminary
    #drawCMS(-1, "Work in Progress", year=year, suppressCMS=True)
    drawCMS(-1, "", year=year, suppressCMS=True)
    drawAnalysis("")

    suffix = ""
    if separate: suffix = "_sep"

    c1.Print("plots/Efficiency/trigger_"+year+suffix+".pdf") 
    c1.Print("plots/Efficiency/trigger_"+year+suffix+".png") 

def btag_efficiency(cut, year, pT_range=None):
    ### Preliminary Operations ###
    from root_numpy import hist2array
    from sklearn.metrics import roc_curve
    import numpy as np
    genPoints = [1600, 1800, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000, 8000]
    signal = ['ZpBB_M'+str(x) for x in genPoints]
    btag_vars = BTAGGEFFVARS
    nbins = 100
    min_, max_ = 0., 1.   
 
    treeRead = True
    channel = cut
    isAH = False 
    for k in sorted(alias.keys(), key=len, reverse=True):
        if k in cut: 
            cut = cut.replace(k, aliasSM[k])
    
    ### Create and fill MC histograms ###
    # Create dict
    file = {}
    tree = {}
    hist = {}
    
    ### Create and fill MC histograms ###
    for i, s in enumerate(back+signal):
        tree[s] = TChain("tree")
        for j, ss in enumerate(sample[s]['files']):
            if year=="run2" or year in ss:
                ### to run on big ntuples:
                #k = 0
                #while True:
                #    if os.path.exists("/eos/user/m/msommerh/Zprime_to_bb_analysis/" + ss + "/" + ss+ "_flatTuple_{}.root".format(k)):
                #        tree[s].Add("/eos/user/m/msommerh/Zprime_to_bb_analysis/" + ss + "/" + ss + "_flatTuple_{}.root".format(k))
                #        k += 1
                #    else:
                #        print "found {} files for sample:".format(k), ss
                #        break
                #if k == 0:
                #    print '  WARNING: files for sample', ss , 'do not exist, continuing'
                #    return True 
                ### end big ntuples
                tree[s].Add(NTUPLEDIR + ss + ".root") ## to run on skimmed ntuples
        for var in btag_vars:
            hist[s+"_"+var] = TH1F(s+"_"+var, ";efficiency; mistag rate", nbins, min_, max_)
            for suf in ["_1", "_2"]: 
                temp_hist = TH1F(s+"_"+var+suf, ";efficiency; mistag rate", nbins, min_, max_)
                temp_hist.Sumw2()
                if pT_range is not None:
                    pT_cut = " && jpt"+suf+">="+str(pT_range[0])+" && jpt"+suf+"<"+str(pT_range[1])
                else:  
                    pT_cut = ""
                if s in signal:
                    flavourcut = " && abs(jflavour"+suf+")==5"
                else:
                    flavourcut = " && (abs(jflavour"+suf+")<4 || abs(jflavour"+suf+")==9 || abs(jflavour"+suf+")==21)" ## FIXME this currently excludes charms
                if len(cut)==0: flavourcut = flavourcut[4:]
                cutstring = "(eventWeightLumi)" + "*("+cut+flavourcut+pT_cut+")"
                tree[s].Project(s+"_"+var+suf, var+suf, cutstring)
                if not tree[s].GetTree()==None: hist[s+"_"+var].SetOption("%s" % tree[s].GetTree().GetEntriesFast())
                #hist[s][var+suf].Scale(sample[s]['weight'] if hist[s].Integral() >= 0 else 0)
                hist[s+"_"+var].Add(temp_hist)
                temp_hist.Delete() 

    fpr = {}
    tpr = {}
    thr = {}
    for var in btag_vars:
        hist_sig = TH1F(var+"_sig", ";efficiency; mistag rate", nbins, min_, max_) 
        hist_bkg = TH1F(var+"_bkg", ";efficiency; mistag rate", nbins, min_, max_) 
        for i, s in enumerate(signal):
            hist_sig.Add(hist[s+"_"+var])
        for i, s in enumerate(back):
            hist_bkg.Add(hist[s+"_"+var])
        sig_arr, sig_edges = hist2array(hist_sig, return_edges=True)
        bkg_arr, bkg_edges = hist2array(hist_bkg, return_edges=True)
        assert len(sig_edges[0]) == len(bkg_edges[0])
        vals = []
        sig_weights = []
        bkg_weights = []
        for j, entry in enumerate(sig_edges[0][:-1]):
            vals.append(0.5*(sig_edges[0][j]+sig_edges[0][j+1]))
            sig_weights.append(sig_arr[j])
            bkg_weights.append(bkg_arr[j])
        sig_labels = np.ones(len(sig_weights))
        bkg_labels = np.zeros(len(bkg_weights))
        fpr[var], tpr[var], thr[var] = roc_curve(np.concatenate((sig_labels, bkg_labels)), np.array(vals+vals), sample_weight=np.concatenate((sig_weights,bkg_weights)))
    
    canv = TCanvas('c', 'c', 500, 650)
    canv.SetGrid()

    graphs = {}
    for j, var in enumerate(btag_vars):
        graphs[var] = TGraph(len(tpr[var]), tpr[var], fpr[var])
        graphs[var].SetLineColor(btag_colors[var])
        graphs[var].SetMarkerStyle(1)
        graphs[var].SetMarkerColor(btag_colors[var])
        graphs[var].SetLineWidth(2)

        graphs[var].SetTitle(";b tagging efficiency;mistag rate (udsg jets)")
        graphs[var].GetXaxis().SetLimits(0.,1.)
        graphs[var].GetHistogram().SetMinimum(1e-4)
        graphs[var].GetHistogram().SetMaximum(1.)
        graphs[var].GetYaxis().SetTitleOffset(1.4)
    leg = TLegend(0.65, 0.15, 0.9, 0.35)
    for j, var in enumerate(btag_vars):
        leg.AddEntry(graphs[var], btag_titles[var])
        if j==0:
            graphs[var].Draw("APL")
        else:
            graphs[var].Draw("PL SAME")
    
    latex = TLatex(0.05, 0.5, str(pT_range[0])+'<p_{T}<'+str(pT_range[1])+' GeV')
    latex.SetTextSize(0.043)
    latex.Draw()

    leg.Draw()
    canv.SetLogy()

    if pT_range is not None:
        pt_suff = "pT{}to{}".format(pT_range[0], pT_range[1])
    else:
        pt_suff = "incl_pT"
    canv.Print("plots/btag_eff/ROC_{}_{}.png".format(year,pt_suff))
    canv.Print("plots/btag_eff/ROC_{}_{}.pdf".format(year,pt_suff))

 
if options.efficiency:
    efficiency(options.year)
elif options.acceptance:
    acceptance(options.year)
elif options.trigger:
    if not SEPARATE:
        trigger_efficiency(options.year, separate=False)
    else:
        trigger_efficiency(options.year, separate=True)
elif options.btagging_eff:
    pt_ranges = [(30,200),(200,400),(400,600),(600,800),(800,1000),(1000,1400),(1400,1800),(1800,2200),(2200,2600),(2600,3000)]
    for pt_range in pt_ranges:
        btag_efficiency(options.cut, options.year, pT_range=pt_range)
else:
    plot(options.variable, options.cut, options.year)

