#! /usr/bin/env python

import os, multiprocessing
import copy
import math
from array import array
from ROOT import ROOT, gROOT, gStyle, gRandom, TSystemDirectory
from ROOT import TFile, TChain, TTree, TCut, TF1, TH1F, TH2F, THStack
from ROOT import TGraph, TGraphErrors, TGraphAsymmErrors, TVirtualFitter
from ROOT import TStyle, TCanvas, TPad
from ROOT import TLegend, TLatex, TText, TLine

from samples import sample
from variables import variable
from aliases import alias, aliasSM, deepFlavour, working_points
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
(options, args) = parser.parse_args()

########## SETTINGS ##########

gROOT.SetBatch(True)
#gROOT.ProcessLine("TSystemDirectory::SetDirectory(0)")
#gROOT.ProcessLine("TH1::AddDirectory(kFALSE);")
gStyle.SetOptStat(0)
#TSystemDirectory.SetDirectory(0)

BTAGGING    = options.btagging
NTUPLEDIR   = "/afs/cern.ch/work/m/msommerh/public/Zprime_to_bb_Analysis/Skim/"
ACCEPTANCEDIR = "/afs/cern.ch/work/m/msommerh/public/Zprime_to_bb_Analysis/acceptance/"
SIGNAL      = 1 # Signal magnification factor
RATIO       = 4 # 0: No ratio plot; !=0: ratio between the top and bottom pads
NORM        = options.norm
PARALLELIZE = False
BLIND       = False
LUMI        = {"run2" : 137190, "2016" : 35920, "2017" : 41530, "2018" : 59740}
ADDSELECTION= options.selection!=""
#XRANGE      = (1400., 9000.)

color = {'none': 920, 'qq': 1, 'bq': 632, 'bb': 600}
color_shift = {'none': 2, 'qq': 922, 'bq': 2, 'bb': 2}
if options.selection not in SELECTIONS.keys():
    print "invalid selection!"
    sys.exit()

########## SAMPLES ##########
data = ["data_obs"]
back = ["TTbar", "QCD"]
#back = ["VV", "ST", "TTbarSL", "WJetsToLNu_HT", "DYJetsToNuNu_HT", "DYJetsToLL_HT"]
sign = ['ZpBB_M2000', 'ZpBB_M4000', 'ZpBB_M6000']#, 'ZpBB_M8000']
#sign = ['ZpBB_M1000', 'ZpBB_M1200', 'ZpBB_M1400', 'ZpBB_M1600', 'ZpBB_M1800', 'ZpBB_M2000', 'ZpBB_M2500', 'ZpBB_M3000', 'ZpBB_M3500', 'ZpBB_M4000', 'ZpBB_M4500', 'ZpBB_M5000', 'ZpBB_M5500', 'ZpBB_M6000', 'ZpBB_M7000', 'ZpBB_M8000']
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
                #if k in cut: cut = cut.replace(k, aliasSM[k].format(b_threshold_medium=deepFlavour['medium'][year], b_threshold_loose=deepFlavour['loose'][year]))              
                if k in cut: 
                    if ADDSELECTION:
                        cut = cut.replace(k, aliasSM[k]+SELECTIONS[options.selection])
                    else:
                        cut = cut.replace(k, aliasSM[k])
        
            else:
                #if k in cut: cut = cut.replace(k, alias[k].format(b_threshold=deepFlavour[BTAGGING][year]))
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
            else: hist[s] = TH1F(s, ";"+variable[var]['title'], len(variable[var]['bins'])-1, array('f', variable[var]['bins']))
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
    
    # X_mass rebin
#    if var=='X_mass' or var=='X_tmass':
#        if 'XZhnn' in channel: rebin = 10
#        elif 'XWh' in channel: rebin = 5
#        else: rebin = 2
#        for i, s in enumerate(data+back+sign): hist[s].Rebin(rebin)
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
    
    # Create stack
    bkg = THStack("Bkg", ";"+hist['BkgSum'].GetXaxis().GetTitle()+";Events / ( "+str((variable[var]['max']-variable[var]['min'])/variable[var]['nbins'])+unit+" )")
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
    
    log = "log" in hist['BkgSum'].GetZaxis().GetTitle()
    if log: c1.GetPad(bool(RATIO)).SetLogy()
        
    # Draw
    bkg.Draw("HIST") # stack
    hist['BkgSum'].Draw("SAME, E2") # sum of bkg
    if not isBlind and len(data) > 0: hist['data_obs'].Draw("SAME, PE") # data
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
    bkg.GetXaxis().SetRangeUser(variable[var]['min'], variable[var]['max'])  ## newly inserted 
 
    #if log: bkg.SetMinimum(1)
    leg.Draw()
    drawCMS(LUMI[year], "Preliminary")
    drawRegion('XVH'+channel, True)
    drawAnalysis(channel)
    
    #if nm1 and not cutValue is None: drawCut(cutValue, bkg.GetMinimum(), bkg.GetMaximum()) #FIXME
    #if len(sign) > 0:
    #    if channel.startswith('X') and len(sign)>0: drawNorm(0.9-0.05*(leg.GetNRows()+1), "#sigma(X) = %.1f pb" % 1.)
    
    setHistStyle(bkg, 1.2 if RATIO else 1.1)
    setHistStyle(hist['BkgSum'], 1.2 if RATIO else 1.1)
       
    if RATIO:
        c1.cd(2)
        err = hist['BkgSum'].Clone("BkgErr;")
        err.SetTitle("")
        err.GetYaxis().SetTitle("Data / Bkg")
        err.GetXaxis().SetRangeUser(variable[var]['min'], variable[var]['max'])  ## newly inserted     
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
        if "b" in channel: suffix+="_"+BTAGGING
        if ADDSELECTION: suffix+="_"+options.selection
        c1.Print("plots/"+channel+"/"+varname+"_"+year+suffix+".png")
        c1.Print("plots/"+channel+"/"+varname+"_"+year+suffix+".pdf")
    
    # Print table
    printTable(hist, sign)
    
    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")

    
########## ######## ##########


def plotAll():
    gROOT.SetBatch(True)
    
    hists = {}
    
    file = TFile(NTUPLEDIR + "TT.root", 'READ')
    file.cd()
    # Looping over file content
    for key in file.GetListOfKeys():
        obj = key.ReadObj()
        # Histograms
        if obj.IsA().InheritsFrom('TH1'): continue
        #    hists.append(obj.GetName())
        # Tree
        elif obj.IsA().InheritsFrom('TTree'): continue
        # Directories
        if obj.IsFolder() and (obj.GetName().endswith('qq') or len(obj.GetName())==2):
            subdir = obj.GetName()
            hists[subdir] = []
            file.cd(subdir)
            for subkey in file.GetDirectory(subdir).GetListOfKeys():
                subobj = subkey.ReadObj()
                if subobj.IsA().InheritsFrom('TH1'):
                    hists[subdir].append(subobj.GetName())
            file.cd('..')
    file.Close() 
    
    for c, l in hists.iteritems():
        #if not os.path.exists("plots/"+c):
        #    os.mkdir("plots/"+c)
        if 'qqqq' in c: continue
        if not len(c) > 2: continue
        if not 'nn' in c: continue
        for h in l:
            plot(h, c)


def efficiency(year):
    genPoints = [1800, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000, 8000]
    eff = {}
    if ADDSELECTION: eff_add = {}
    
    channels = ['none', 'qq', 'bq', 'bb']

    for channel in channels:
        treeSign = {}
        ngenSign = {}
        nevtSign = {}
        eff[channel] = TGraphErrors()
        if ADDSELECTION:
            nevtSign_add = {}
            eff_add[channel] = TGraphErrors()

        for i, m in enumerate(genPoints):
            signName = "ZpBB_M"+str(m)
            ngenSign[m] = 0.
            nevtSign[m] = 0.
            if ADDSELECTION: nevtSign_add[m] = 0.
            for j, ss in enumerate(sample[signName]['files']):
                if year=="run2" or year in ss:
                    sfile = TFile(NTUPLEDIR + ss + ".root", "READ")
                    if year=='run2':
                        if '2016' in ss:
                            ngenSign[m] += sample[signName]['genEvents']['2016']
                        elif '2017' in ss:
                            ngenSign[m] += sample[signName]['genEvents']['2017']
                        elif '2018' in ss:
                            ngenSign[m] += sample[signName]['genEvents']['2018']
                        else:
                            print "ATTENTION!!! Undefinded year in sample:", ss
                    else:
                        ngenSign[m] += sample[signName]['genEvents'][year]
                    treeSign[m] = sfile.Get("tree")
                    if BTAGGING=='semimedium':
                        nevtSign[m] += treeSign[m].GetEntries(aliasSM[channel])
                        if ADDSELECTION: nevtSign_add[m] += treeSign[m].GetEntries(aliasSM[channel]+SELECTIONS[options.selection])
                    else:
                        nevtSign[m] += treeSign[m].GetEntries(alias[channel].format(WP=working_points[BTAGGING]))
                        if ADDSELECTION: nevtSign_add[m] += treeSign[m].GetEntries(alias[channel].format(WP=working_points[BTAGGING])+SELECTIONS[options.selection])
                    sfile.Close()
                    #print channel, ss, ":", nevtSign[m], "/", ngenSign[m], "=", nevtSign[m]/ngenSign[m]
            if nevtSign[m] == 0 or ngenSign[m] < 0: continue
            n = eff[channel].GetN()
            eff[channel].SetPoint(n, m, nevtSign[m]/ngenSign[m])
            eff[channel].SetPointError(n, 0, math.sqrt(nevtSign[m])/ngenSign[m])
            if ADDSELECTION:
                eff_add[channel].SetPoint(n, m, nevtSign_add[m]/ngenSign[m])
                eff_add[channel].SetPointError(n, 0, math.sqrt(nevtSign_add[m])/ngenSign[m])

        eff[channel].SetMarkerColor(color[channel])
        eff[channel].SetMarkerStyle(20)
        eff[channel].SetLineColor(color[channel])
        eff[channel].SetLineWidth(2)

        if ADDSELECTION:
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
    
    if ADDSELECTION:
        eff_add["sum"] = TGraphErrors(n)
        eff_add["sum"].SetMarkerStyle(25)
        eff_add["sum"].SetMarkerColor(1)
        eff_add["sum"].SetLineWidth(2)
        eff_add["sum"].SetLineStyle(7)

    for i in range(n):
        tot, mass = 0., 0.
        if ADDSELECTION: tot_add = 0.
        for channel in channels:
            if channel=='qq' or channel=='none': continue
            if eff[channel].GetN() > i:
                tot += eff[channel].GetY()[i]
                if ADDSELECTION: tot_add += eff_add[channel].GetY()[i]
                mass = eff[channel].GetX()[i]
                if tot > maxEff: maxEff = tot
        eff["sum"].SetPoint(i, mass, tot)
        if ADDSELECTION: eff_add["sum"].SetPoint(i, mass, tot_add)


    leg = TLegend(0.15, 0.60, 0.95, 0.8)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0) #1001
    leg.SetFillColor(0)
    leg.SetNColumns(len(channels)/4)
    for i, channel in enumerate(channels):
        if eff[channel].GetN() > 0: 
            leg.AddEntry(eff[channel], getChannel(channel), "pl")
            if ADDSELECTION: leg.AddEntry(eff_add[channel], getChannel(channel)+" "+options.selection, "pl") 
    if ADDSELECTION: 
        leg.SetY1(leg.GetY2()-len([x for x in channels if eff[x].GetN() > 0])*0.045)
    else:
        leg.SetY1(leg.GetY2()-len([x for x in channels if eff[x].GetN() > 0])/2.*0.045)
    legS = TLegend(0.5, 0.85-0.045, 0.9, 0.85)
    legS.SetBorderSize(0)
    legS.SetFillStyle(0) #1001
    legS.SetFillColor(0)
    legS.AddEntry(eff['sum'], "Total efficiency (1 b tag + 2 b tag)", "pl")
    if ADDSELECTION: legS.AddEntry(eff_add['sum'], "Total efficiency (1 b tag + 2 b tag) "+options.selection, "pl")
    c1 = TCanvas("c1", "Signal Efficiency", 1200, 800)
    c1.cd(1)
    eff['sum'].Draw("APL")
    if ADDSELECTION: eff_add['sum'].Draw("SAME, PL")
    for i, channel in enumerate(channels): 
        eff[channel].Draw("SAME, PL")
        if ADDSELECTION: eff_add[channel].Draw("SAME, PL")
    leg.Draw()
    legS.Draw()
    setHistStyle(eff["sum"], 1.1)
    eff["sum"].SetTitle(";m_{Z'} (GeV);Acceptance #times efficiency")
    eff["sum"].SetMinimum(0.)
    eff["sum"].SetMaximum(max(1., maxEff*1.5)) #0.65
    if ADDSELECTION: 
        eff_add["sum"].SetTitle(";m_{Z'} (GeV);Acceptance #times efficiency")
        eff_add["sum"].SetMinimum(0.)
        eff_add["sum"].SetMaximum(1.)

    eff["sum"].GetXaxis().SetTitleSize(0.045)
    eff["sum"].GetYaxis().SetTitleSize(0.045)
    eff["sum"].GetYaxis().SetTitleOffset(1.1)
    eff["sum"].GetXaxis().SetTitleOffset(1.05)
    eff["sum"].GetXaxis().SetRangeUser(1500, 8000)
    c1.SetTopMargin(0.05)
    drawCMS(-1, "Simulation Preliminary", year=year) #Preliminary
    drawAnalysis("")

    if ADDSELECTION:
        c1.Print("plots/Efficiency/"+year+"_"+BTAGGING+"_"+options.selection+".pdf") 
        c1.Print("plots/Efficiency/"+year+"_"+BTAGGING+"_"+options.selection+".png") 
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
    eff = TGraphErrors()

    for i, m in enumerate(genPoints):
        ngenSign[m] = 0.
        nevtSign[m] = 0.

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
            nEvents = passing_events_hist.GetBinContent(1)
            nevtSign[m] += nEvents

            sfile.Close()
        
        print m, ":", nevtSign[m], "/", ngenSign[m], "=", nevtSign[m]/ngenSign[m]
        if nevtSign[m] == 0 or ngenSign[m] < 0: continue
        n = eff.GetN()
        eff.SetPoint(n, m, nevtSign[m]/ngenSign[m])
        eff.SetPointError(n, 0, math.sqrt(nevtSign[m])/ngenSign[m])

    eff.SetMarkerColor(4)
    eff.SetMarkerStyle(20)
    eff.SetLineColor(4)
    eff.SetLineWidth(2)

    n = eff.GetN()
    maxEff = 0.

    #leg = TLegend(0.15, 0.60, 0.95, 0.8)
    #leg.SetBorderSize(0)
    #leg.SetFillStyle(0) #1001
    #leg.SetFillColor(0)
    #leg.SetY1(leg.GetY2()-len([x for x in channels if eff[x].GetN() > 0])/2.*0.045)

    #legS = TLegend(0.5, 0.85-0.045, 0.9, 0.85)
    #legS.SetBorderSize(0)
    #legS.SetFillStyle(0) #1001
    #legS.SetFillColor(0)
    #legS.AddEntry(eff['sum'], "Total efficiency (1 b tag + 2 b tag)", "pl")

    c1 = TCanvas("c1", "Signal Acceptance", 1200, 800)
    c1.cd(1)
    eff.Draw("APL")
    #leg.Draw()
    #legS.Draw()
    #setHistStyle(eff["sum"], 1.1)
    eff.SetTitle(";m_{Z'} (GeV);Acceptance")
    eff.SetMinimum(0.)
    eff.SetMaximum(max(1., maxEff*1.5)) #0.65

    eff.GetXaxis().SetTitleSize(0.045)
    eff.GetYaxis().SetTitleSize(0.045)
    eff.GetYaxis().SetTitleOffset(1.1)
    eff.GetXaxis().SetTitleOffset(1.05)
    eff.GetXaxis().SetRangeUser(1500, 8000)
    c1.SetTopMargin(0.05)
    drawCMS(-1, "Simulation Preliminary", year=year) #Preliminary
    drawAnalysis("")

    c1.Print("plots/Efficiency/"+year+"_Acceptance.pdf") 
    c1.Print("plots/Efficiency/"+year+"_Acceptance.png") 


#if options.all: plotAll()
#elif options.norm: plotNorm(options.variable, options.cut)
#elif options.top: plotTop()
if options.efficiency:
    efficiency(options.year)
elif options.acceptance:
    acceptance(options.year)
else:
    plot(options.variable, options.cut, options.year)

