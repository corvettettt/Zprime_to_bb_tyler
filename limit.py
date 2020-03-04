#! /usr/bin/env python

###
### Macro for creating the exclusion limits plots from the combine outputs.
###

import os, sys, getopt
import copy
import time
import math
from array import array
from ROOT import gROOT, gRandom
from ROOT import TFile, TTree, TCut, TH1F, TH2F, TGraph, TGraph2D, TGraphErrors, TGraphAsymmErrors
from ROOT import TStyle, TCanvas, TPad
from ROOT import TLegend, TLatex, TText, TColor

#from DMPD.Heppy.tools.samples import *
from utils import *
from theoryXs import HVT, SSM

#from thdmXs import THDM

# Combine output
# 0 - Observed Limit
# 1 - Expected  2.5%
# 2 - Expected 16.0%
# 3 - Expected 50.0%
# 4 - Expected 84.0%
# 5 - Expected 97.5%
# 6 - Significance
# 7 - p-value
# 8 - Best fit r
# 9 - Best fit r down
#10 - Best fit r up

import optparse
usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage)
parser.add_option("-y", "--year", action="store", type="string", dest="year",default="2017")
parser.add_option("-M", "--isMC", action="store_true", default=False, dest="isMC")
parser.add_option("-c", "--category", action="store", type="string", dest="category", default="")
parser.add_option("-B", "--blind", action="store_true", default=False, dest="blind")
parser.add_option("-b", "--btagging", action="store", type="string", dest="btagging", default="medium")
parser.add_option("-A", "--Acceptance", action="store_true", default=False, dest="Acceptance")
(options, args) = parser.parse_args()
 
gStyle.SetOptStat(0)

gROOT.SetBatch(True)

luminosities = {'2016':35920., '2017':41530., '2018':59740., 'run2':137190.}

#HTOBB       = 0.5824#0.577
ZPTOBB      = 1.
LUMI        = 35867
MAXIMUM     = {'XVHsl' : 4500., 'XWHsl' : 4500., 'XZHsl' : 3500., 'bb':100}
BTAGGING    = options.btagging
YEAR        = options.year
ISMC        = options.isMC
CATEGORY    = options.category
INCLUDEACC  = options.Acceptance

CAT_LABELS  = {'bb': "2 b tag", 'bq': "1 b tag", 'mumu': "2 #mu"}

if YEAR not in ['2016', '2017', '2018', 'run2', 'run2c']:
    print "unknown year:", YEAR
    sys.exit()

if BTAGGING not in ['tight', 'medium', 'loose', 'semimedium']:
    print "unknown btagging requirement:", BTAGGING
    sys.exit()

if CATEGORY not in ['', 'bb', 'bq', 'mumu']:
    print "unknown btagging category"
    sys.exit()

if YEAR=='run2c':
    YEAR='run2'
    SY=True
    print "Plotting the result from combine on separate years for run2..."
else:
    SY=False

LUMI        = luminosities[YEAR]

SIGNALS = range(1600, 8000+1, 100)

ACCEPTANCE = {}
for s in range(500,9000+1,100): ACCEPTANCE[s] = 0.405 ##FIXME could include mass dependent exact value FIXME

theoryLabel = {'B3' : "HVT model B (g_{V}=3)", 'A1' : "HVT model A (g_{V}=1)", "SSM" : "SSM Z'"}
theoryLineColor = {'B3' : 629, 'A1' : 616-3, "SSM" : 602}
theoryFillColor = {'B3' : 625, 'A1' : 616-7, 'SSM' : 856}
theoryFillStyle = {'B3' : 3002, 'A1' : 3013, 'SSM' : 3013}


def fillValues(filename):
    val = {}
    mass = []
    for i, s in enumerate(SIGNALS):
        try:
            file = open(filename % s, 'r')
            if file==None:
                print "Signal", filename % s, "does not exist"
                continue
            val[s] = file.read().splitlines()
            if len(val[s]) <= 1:
                #signals.remove(s)
                print "Signal", filename % s, "has no values"
                continue
            for i, f in enumerate(val[s]): val[s][i] = float(val[s][i])
            if 'fullCls' in filename: val[1:5]=sorted(val[1:5])
            if not s in mass: mass.append(s)
        except:
            print "File", filename % s, "does not exist"
            pass
    return mass, val


def limit():
    method = ''
    channel = "bb"
    if INCLUDEACC:
        particleP = "X"
    else:
        particleP = "Z'"
    particle = 'b#bar{b}'
    multF = ZPTOBB
    THEORY = ['A1', 'B3']
    if INCLUDEACC: THEORY.append('SSM')
 
    suffix = "_"+BTAGGING
    if ISMC: suffix += "_MC"
    if SY: suffix += "_comb"
    #if method=="cls": suffix="_CLs"
    if INCLUDEACC: suffix+="_acc"

    if SY:
        filename = "./combine/limits/" + BTAGGING + "/combined_run2/"+ YEAR + "_M%d.txt"
    else:
        filename = "./combine/limits/" + BTAGGING + "/"+ YEAR + "_M%d.txt"
    if CATEGORY!="":
        if SY:
            filename = filename.replace(BTAGGING + "/combined_run2/", BTAGGING + "/single_category/combined_run2/"+CATEGORY+"_")
        else:
            filename = filename.replace(BTAGGING + "/", BTAGGING + "/single_category/"+CATEGORY+"_")
        suffix += "_"+CATEGORY
    if ISMC: filename = filename.replace(".txt", "_MC.txt")
    mass, val = fillValues(filename)

    #print "mass =",mass
    #print "val =", val

    Obs0s = TGraph()
    Exp0s = TGraph()
    Exp1s = TGraphAsymmErrors()
    Exp2s = TGraphAsymmErrors()
    Sign = TGraph()
    pVal = TGraph()
    Best = TGraphAsymmErrors()
    Theory = {}

    for i, m in enumerate(mass):
        if not m in val:
            print "Key Error:", m, "not in value map"
            continue

        if INCLUDEACC:
            acc_factor = ACCEPTANCE[m]
        else:
            acc_factor = 1.

        n = Exp0s.GetN()
        Obs0s.SetPoint(n, m, val[m][0]*multF*acc_factor)
        Exp0s.SetPoint(n, m, val[m][3]*multF*acc_factor)
        Exp1s.SetPoint(n, m, val[m][3]*multF*acc_factor)
        Exp1s.SetPointError(n, 0., 0., (val[m][3]-val[m][2])*multF*acc_factor, (val[m][4]-val[m][3])*multF*acc_factor)
        Exp2s.SetPoint(n, m, val[m][3]*multF*acc_factor)
        Exp2s.SetPointError(n, 0., 0., (val[m][3]-val[m][1])*multF*acc_factor, (val[m][5]-val[m][3])*multF*acc_factor)
        if len(val[m]) > 6: Sign.SetPoint(n, m, val[m][6])
        if len(val[m]) > 7: pVal.SetPoint(n, m, val[m][7])
        if len(val[m]) > 8: Best.SetPoint(n, m, val[m][8])
        if len(val[m]) > 10: Best.SetPointError(n, 0., 0., abs(val[m][9]), val[m][10])


    for t in THEORY:
        Theory[t] = TGraphAsymmErrors()
        Xs_dict = HVT[t]['Z']['XS'] if t!='SSM' else SSM['Z']
        for m in sorted(Xs_dict.keys()):
            if INCLUDEACC and t!='SSM':
                acc_factor = ACCEPTANCE[m]
            else:
                acc_factor = 1.
            if m < SIGNALS[0] or m > SIGNALS[-1]: continue
            #if m < mass[0] or m > mass[-1]: continue
            #if t!= 'SSM' and m>4500: continue ## I don't have the higher mass xs
            if m>4500: continue
            XsZ, XsZ_Up, XsZ_Down = 0., 0., 0.
            if t!='SSM':
                XsZ = 1000.*HVT[t]['Z']['XS'][m]*SSM["BrZ"][m] #assuming the same BR as the SSM Z' one
                XsZ_Up = XsZ*(1.+math.hypot(HVT[t]['Z']['QCD'][m][0]-1., HVT[t]['Z']['PDF'][m][0]-1.))
                XsZ_Down = XsZ*(1.-math.hypot(1.-HVT[t]['Z']['QCD'][m][0], 1.-HVT[t]['Z']['PDF'][m][0]))
            else:
                XsZ = 1000.*SSM['Z'][m]*SSM["BrZ"][m]
                XsZ_Up = XsZ*(1.+math.hypot(HVT['A1']['Z']['QCD'][m][0]-1., HVT['A1']['Z']['PDF'][m][0]-1.))
                XsZ_Down = XsZ*(1.-math.hypot(1.-HVT['A1']['Z']['QCD'][m][0], 1.-HVT['A1']['Z']['PDF'][m][0]))
     
            n = Theory[t].GetN()
            Theory[t].SetPoint(n, m, XsZ*acc_factor)
            Theory[t].SetPointError(n, 0., 0., (XsZ-XsZ_Down)*acc_factor, (XsZ_Up-XsZ)*acc_factor)

            Theory[t].SetLineColor(theoryLineColor[t])
            Theory[t].SetFillColor(theoryFillColor[t])
            Theory[t].SetFillStyle(theoryFillStyle[t])
            Theory[t].SetLineWidth(2)
            #Theory[t].SetLineStyle(7)


    Exp2s.SetLineWidth(2)
    Exp2s.SetLineStyle(1)
    Obs0s.SetLineWidth(3)
    Obs0s.SetMarkerStyle(0)
    Obs0s.SetLineColor(1)
    Exp0s.SetLineStyle(2)
    Exp0s.SetLineWidth(3)
    Exp1s.SetFillColor(417) #kGreen+1
    Exp1s.SetLineColor(417) #kGreen+1
    Exp2s.SetFillColor(800) #kOrange
    Exp2s.SetLineColor(800) #kOrange
    Exp2s.GetXaxis().SetTitle("m_{"+particleP+"} (GeV)")
    Exp2s.GetXaxis().SetTitleSize(Exp2s.GetXaxis().GetTitleSize()*1.25)
    Exp2s.GetXaxis().SetNoExponent(True)
    Exp2s.GetXaxis().SetMoreLogLabels(True)
    Exp2s.GetYaxis().SetTitle("#sigma("+particleP+") #bf{#it{#Beta}}("+particleP+" #rightarrow "+particle+"){} (fb)".format(" #times #Alpha" if INCLUDEACC else ""))
    Exp2s.GetYaxis().SetTitleOffset(1.5)
    Exp2s.GetYaxis().SetNoExponent(True)
    Exp2s.GetYaxis().SetMoreLogLabels()

    Sign.SetLineWidth(2)
    Sign.SetLineColor(629)
    Sign.GetXaxis().SetTitle("m_{"+particleP+"} (GeV)")
    Sign.GetXaxis().SetTitleSize(Sign.GetXaxis().GetTitleSize()*1.1)
    Sign.GetYaxis().SetTitle("Significance")

    pVal.SetLineWidth(2)
    pVal.SetLineColor(629)
    pVal.GetXaxis().SetTitle("m_{"+particleP+"} (GeV)")
    pVal.GetXaxis().SetTitleSize(pVal.GetXaxis().GetTitleSize()*1.1)
    pVal.GetYaxis().SetTitle("local p-Value")

    Best.SetLineWidth(2)
    Best.SetLineColor(629)
    Best.SetFillColor(629)
    Best.SetFillStyle(3003)
    Best.GetXaxis().SetTitle("m_{"+particleP+"} (GeV)")
    Best.GetXaxis().SetTitleSize(Best.GetXaxis().GetTitleSize()*1.1)
    Best.GetYaxis().SetTitle("Best Fit (pb)")



    c1 = TCanvas("c1", "Exclusion Limits", 800, 600)
    c1.cd()
    #SetPad(c1.GetPad(0))
    c1.GetPad(0).SetTopMargin(0.06)
    c1.GetPad(0).SetRightMargin(0.05)
    c1.GetPad(0).SetLeftMargin(0.12)
    c1.GetPad(0).SetTicks(1, 1)
    #c1.GetPad(0).SetGridx()
    #c1.GetPad(0).SetGridy()
    c1.GetPad(0).SetLogy()
    Exp2s.Draw("A3")
    Exp1s.Draw("SAME, 3")
    for t in THEORY:
        Theory[t].Draw("SAME, L3")
        Theory[t].Draw("SAME, L3X0Y0")
    Exp0s.Draw("SAME, L")
    if not options.blind: Obs0s.Draw("SAME, L")
    #setHistStyle(Exp2s)
    Exp2s.GetXaxis().SetTitleSize(0.050)
    Exp2s.GetYaxis().SetTitleSize(0.050)
    Exp2s.GetXaxis().SetLabelSize(0.045)
    Exp2s.GetYaxis().SetLabelSize(0.045)
    Exp2s.GetXaxis().SetTitleOffset(0.90)
    Exp2s.GetYaxis().SetTitleOffset(1.25)
    Exp2s.GetYaxis().SetMoreLogLabels(True)
    Exp2s.GetYaxis().SetNoExponent(True)
    if INCLUDEACC:
        Exp2s.GetYaxis().SetRangeUser(0.05, 5.e3)
    else:
        Exp2s.GetYaxis().SetRangeUser(0.1, 5.e3)
    #else: Exp2s.GetYaxis().SetRangeUser(0.1, 1.e2)
    #Exp2s.GetXaxis().SetRangeUser(mass[0], min(mass[-1], MAXIMUM[channel] if channel in MAXIMUM else 1.e6))
    Exp2s.GetXaxis().SetRangeUser(SIGNALS[0], SIGNALS[-1])
    #drawAnalysis(channel)
    drawAnalysis("")
    #drawRegion(channel, True)
    drawRegion("", True)
    #drawCMS(LUMI, "Simulation Preliminary") #Preliminary
    if CATEGORY=="": 
        #drawCMS(LUMI, "Work in Progress", suppressCMS=True)
        drawCMS(LUMI, "", suppressCMS=True)
    else:
         #drawCMS(LUMI, "Work in Progress, "+CAT_LABELS[CATEGORY], suppressCMS=True)       
         drawCMS(LUMI, CAT_LABELS[CATEGORY], suppressCMS=True)       

    # legend
    top = 0.9
    nitems = 4 + len(THEORY)

    leg = TLegend(0.55, top-nitems*0.3/5., 0.98, top)
    #leg = TLegend(0.45, top-nitems*0.3/5., 0.98, top)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0) #1001
    leg.SetFillColor(0)
    leg.SetHeader("95% CL upper limits")
    leg.AddEntry(Obs0s, "Observed", "l")
    leg.AddEntry(Exp0s, "Expected", "l")
    leg.AddEntry(Exp1s, "#pm 1 std. deviation", "f")
    leg.AddEntry(Exp2s, "#pm 2 std. deviation", "f")
    for t in THEORY: leg.AddEntry(Theory[t], theoryLabel[t], "fl")
    leg.Draw()
    latex = TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.045)
    latex.SetTextFont(42)
    #latex.DrawLatex(0.66, leg.GetY1()-0.045, particleP+" #rightarrow "+particle+"h")

    leg2 = TLegend(0.12, 0.225-2*0.25/5., 0.65, 0.225)
    leg2.SetBorderSize(0)
    leg2.SetFillStyle(0) #1001
    leg2.SetFillColor(0)
    c1.GetPad(0).RedrawAxis()

    leg2.Draw()
    if not options.blind: Obs0s.Draw("SAME, L")
    c1.GetPad(0).Update()

    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")

    c1.Print("combine/plotsLimit/ExclusionLimits/"+YEAR+suffix+".png")
    c1.Print("combine/plotsLimit/ExclusionLimits/"+YEAR+suffix+".pdf")
    if 'ah' in channel or 'sl' in channel:
        c1.Print("combine/plotsLimit/ExclusionLimits/"+YEAR+suffix+".C")
        c1.Print("combine/plotsLimit/ExclusionLimits/"+YEAR+suffix+".root")

    for t in THEORY:
        print "Model", t, ":",
        for m in range(mass[0], mass[-1], 1):
            if not (Theory[t].Eval(m) > Obs0s.Eval(m)) == (Theory[t].Eval(m+1) > Obs0s.Eval(m+1)): print m,
        print ""

    return ##FIXME


    # ---------- Significance ----------
    c2 = TCanvas("c2", "Significance", 800, 600)
    c2.cd()
    c2.GetPad(0).SetTopMargin(0.06)
    c2.GetPad(0).SetRightMargin(0.05)
    c2.GetPad(0).SetTicks(1, 1)
    c2.GetPad(0).SetGridx()
    c2.GetPad(0).SetGridy()
    Sign.GetYaxis().SetRangeUser(0., 5.)
    Sign.Draw("AL3")
    #drawCMS(LUMI, "Preliminary")
    drawCMS(LUMI, "Work in Progress", suppressCMS=True)
    drawAnalysis(channel[1:3])
    c2.Print("combine/plotsLimit/Significance/"+YEAR+suffix+".png")
    c2.Print("combine/plotsLimit/Significance/"+YEAR+suffix+".pdf")
#    c2.Print("plotsLimit/Significance/"+YEAR+suffix+".root")
#    c2.Print("plotsLimit/Significance/"+YEAR+suffix+".C")

    # ---------- p-Value ----------
    c3 = TCanvas("c3", "p-Value", 800, 600)
    c3.cd()
    c3.GetPad(0).SetTopMargin(0.06)
    c3.GetPad(0).SetRightMargin(0.05)
    c3.GetPad(0).SetTicks(1, 1)
    c3.GetPad(0).SetGridx()
    c3.GetPad(0).SetGridy()
    c3.GetPad(0).SetLogy()
    pVal.Draw("AL3")
    pVal.GetYaxis().SetRangeUser(2.e-7, 0.5)

    ci = [1., 0.317310508, 0.045500264, 0.002699796, 0.00006334, 0.000000573303, 0.000000001973]
    line = TLine()
    line.SetLineColor(922)
    line.SetLineStyle(7)
    text = TLatex()
    text.SetTextColor(922)
    text.SetTextSize(0.025)
    text.SetTextAlign(12)
    for i in range(1, len(ci)-1):
        line.DrawLine(pVal.GetXaxis().GetXmin(), ci[i]/2, pVal.GetXaxis().GetXmax(), ci[i]/2);
        text.DrawLatex(pVal.GetXaxis().GetXmax()*1.01, ci[i]/2, "%d #sigma" % i);

    #drawCMS(LUMI, "Preliminary")
    drawCMS(LUMI, "Work in Progress", suppressCMS=True)
    drawAnalysis(channel[1:3])
    c3.Print("combine/plotsLimit/pValue/"+YEAR+suffix+".png")
    c3.Print("combine/plotsLimit/pValue/"+YEAR+suffix+".pdf")
#    c3.Print("plotsLimit/pValue/"+YEAR+suffix+".root")
#    c3.Print("plotsLimit/pValue/"+YEAR+suffix+".C")

    # --------- Best Fit ----------
    c4 = TCanvas("c4", "Best Fit", 800, 600)
    c4.cd()
    c4.GetPad(0).SetTopMargin(0.06)
    c4.GetPad(0).SetRightMargin(0.05)
    c4.GetPad(0).SetTicks(1, 1)
    c4.GetPad(0).SetGridx()
    c4.GetPad(0).SetGridy()
    Best.Draw("AL3")
    #drawCMS(LUMI, "Preliminary")
    drawCMS(LUMI, "Work in Progress", suppressCMS=True)
    drawAnalysis(channel[1:3])
    c4.Print("combine/plotsLimit/BestFit/"+YEAR+suffix+".png")
    c4.Print("combine/plotsLimit/BestFit/"+YEAR+suffix+".pdf")
#    c4.Print("plotsLimit/BestFit/"+YEAR+suffix+".root")
#    c4.Print("plotsLimit/BestFit/"+YEAR+suffix+".C")

    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")

    if 'ah' in channel:
        outFile = TFile("bands.root", "RECREATE")
        outFile.cd()
        pVal.Write("graph")
        Best.Write("best")
        outFile.Close()


def limit2HDM():
    global signals
    signals = range(800, 2000+1, 50)
    multF = HTOBB
    THEORY = ['T1', 'T2']
    
    mass, val = fillValues("./combine/AZh/AZh_M%d.txt")
    Obs0s = TGraph()
    Exp0s = TGraph()
    Exp1s = TGraphAsymmErrors()
    Exp2s = TGraphAsymmErrors()
    
    massB, valB = fillValues("./combine/BBAZh/BBAZh_M%d.txt")
    Obs0sB = TGraph()
    Exp0sB = TGraph()
    Exp1sB = TGraphAsymmErrors()
    Exp2sB = TGraphAsymmErrors()
    
    for i, m in enumerate(mass):
        if not m in val:
            print "Key Error:", m, "not in value map"
            continue

        n = Exp0s.GetN()
        Obs0s.SetPoint(n, m, val[m][0]*multF)
        Exp0s.SetPoint(n, m, val[m][3]*multF)
        Exp1s.SetPoint(n, m, val[m][3]*multF)
        Exp1s.SetPointError(n, 0., 0., val[m][3]*multF-val[m][2]*multF, val[m][4]*multF-val[m][3]*multF)
        Exp2s.SetPoint(n, m, val[m][3]*multF)
        Exp2s.SetPointError(n, 0., 0., val[m][3]*multF-val[m][1]*multF, val[m][5]*multF-val[m][3]*multF)
        
        Obs0sB.SetPoint(n, m, valB[m][0]*multF)
        Exp0sB.SetPoint(n, m, valB[m][3]*multF)
        Exp1sB.SetPoint(n, m, valB[m][3]*multF)
        Exp1sB.SetPointError(n, 0., 0., valB[m][3]*multF-valB[m][2]*multF, valB[m][4]*multF-valB[m][3]*multF)
        Exp2sB.SetPoint(n, m, valB[m][3]*multF)
        Exp2sB.SetPointError(n, 0., 0., valB[m][3]*multF-valB[m][1]*multF, valB[m][5]*multF-valB[m][3]*multF)

    col = 629
    Exp2s.SetLineWidth(2)
    Exp2s.SetLineStyle(1)
    Obs0s.SetLineWidth(3)
    Obs0s.SetMarkerStyle(0)
    Obs0s.SetLineColor(1)
    Exp0s.SetLineStyle(2)
    Exp0s.SetLineWidth(3)
    Exp0s.SetLineColor(1)
#    Exp1s.SetFillColorAlpha(col, 0.4) #kGreen+1
#    Exp1s.SetLineColorAlpha(col, 0.4)
#    Exp2s.SetFillColorAlpha(col, 0.2) #kOrange
#    Exp2s.SetLineColorAlpha(col, 0.2)
    Exp1s.SetFillColor(417)
    Exp1s.SetLineColor(417)
    Exp2s.SetFillColor(800)
    Exp2s.SetLineColor(800)
    
    colB = 922
    Exp2sB.SetLineWidth(2)
    Obs0sB.SetLineStyle(9)
    Obs0sB.SetLineWidth(3)
    Obs0sB.SetMarkerStyle(0)
    Obs0sB.SetLineColor(colB)
    Exp0sB.SetLineStyle(8)
    Exp0sB.SetLineWidth(3)
    Exp0sB.SetLineColor(colB)
    Exp1sB.SetFillColorAlpha(colB, 0.4) #kGreen+1
    Exp1sB.SetLineColorAlpha(colB, 0.4)
    Exp2sB.SetFillColorAlpha(colB, 0.2) #kOrange
    Exp2sB.SetLineColorAlpha(colB, 0.2)
    
    Exp2s.GetXaxis().SetTitle("m_{A} (GeV)")
    Exp2s.GetXaxis().SetTitleSize(Exp2s.GetXaxis().GetTitleSize()*1.25)
    Exp2s.GetXaxis().SetNoExponent(True)
    Exp2s.GetXaxis().SetMoreLogLabels(True)
    Exp2s.GetYaxis().SetTitle("#sigma(A) #bf{#it{#Beta}}(A #rightarrow Zh) #bf{#it{#Beta}}(h #rightarrow bb) (fb)")
    Exp2s.GetYaxis().SetTitleOffset(1.5)
    Exp2s.GetYaxis().SetNoExponent(True)
    Exp2s.GetYaxis().SetMoreLogLabels()
    
    Theory = {}
    #for t in THEORY:
    #    Theory[t] = TGraphAsymmErrors()
    #    for m in sorted(THDM[t]['ggA'].keys()):
    #        if m < mass[0] or m > mass[-1]: continue
    #        Xs, Xs_Up, Xs_Down = 0., 0., 0.
    #        Xs = THDM[t]['ggA'][m]
    #        Xs_Up = Xs*(1.+math.sqrt((THDM['PDF']['ggA'][m][0]-1.)**2 + (THDM['QCD']['ggA'][m][0]-1.)**2))
    #        Xs_Down = Xs*(1.-math.sqrt((1.-THDM['PDF']['ggA'][m][1])**2 + (1.-THDM['QCD']['ggA'][m][1])**2))
    #        n = Theory[t].GetN()
    #        Theory[t].SetPoint(n, m, Xs)
    #        Theory[t].SetPointError(n, 0., 0., (Xs-Xs_Down), (Xs_Up-Xs))

    #    Theory[t].SetLineColor(theoryLineColor[t])
    #    Theory[t].SetFillColor(theoryFillColor[t])
    #    Theory[t].SetFillStyle(theoryFillStyle[t])
    #    Theory[t].SetLineWidth(2)
    #        #Theory[t].SetLineStyle(7)

    c1 = TCanvas("c1", "Exclusion Limits", 800, 600)
    c1.cd()
    #SetPad(c1.GetPad(0))
    c1.GetPad(0).SetTopMargin(0.06)
    c1.GetPad(0).SetRightMargin(0.05)
    c1.GetPad(0).SetLeftMargin(0.12)
    c1.GetPad(0).SetTicks(1, 1)
    c1.GetPad(0).SetLogy()
    Exp2s.Draw("A3")
    Exp1s.Draw("SAME, 3")
    Exp0s.Draw("SAME, L")
#    Exp2sB.Draw("SAME, 3")
#    Exp1sB.Draw("SAME, 3")
    Exp0sB.Draw("SAME, L")
    if not options.blind:
        Obs0s.Draw("SAME, L")
        Obs0sB.Draw("SAME, L")
    for t in THEORY:
        Theory[t].Draw("SAME, L3")
        Theory[t].Draw("SAME, L3X0Y0")
    #setHistStyle(Exp2s)
#    Exp2s.GetXaxis().SetTitleSize(0.045)
#    Exp2s.GetYaxis().SetTitleSize(0.04)
#    Exp2s.GetXaxis().SetLabelSize(0.04)
#    Exp2s.GetYaxis().SetLabelSize(0.04)
#    Exp2s.GetXaxis().SetTitleOffset(1)
#    Exp2s.GetYaxis().SetTitleOffset(1.25)
    Exp2s.GetXaxis().SetTitleSize(0.050)
    Exp2s.GetYaxis().SetTitleSize(0.050)
    Exp2s.GetXaxis().SetLabelSize(0.045)
    Exp2s.GetYaxis().SetLabelSize(0.045)
    Exp2s.GetXaxis().SetTitleOffset(0.90)
    Exp2s.GetYaxis().SetTitleOffset(1.25)
    Exp2s.GetYaxis().SetMoreLogLabels(True)
    Exp2s.GetYaxis().SetNoExponent(True)
    Exp2s.GetYaxis().SetRangeUser(0.5, 1.e3)
    Exp2s.GetXaxis().SetRangeUser(mass[0], mass[-1])
    drawAnalysis('AZh')
    drawRegion('AZHsl', True)
    #drawCMS(LUMI, "") #Preliminary
    drawCMS(LUMI, "Work in Progress", suppressCMS=True)

    # legend
    leg = TLegend(0.6, 0.90, 0.99, 0.90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0) #1001
    leg.SetFillColor(0)
    leg.SetHeader("95% CL upper limits")
    leg.AddEntry(None, "gg #rightarrow A #rightarrow Zh", "") #"95% CL upper limits"
    leg.AddEntry(Obs0s,  "Observed", "l")
    leg.AddEntry(Exp0s,  "Expected", "l")
    leg.AddEntry(Exp1s, "#pm 1 std. deviation", "f")
    leg.AddEntry(Exp2s, "#pm 2 std. deviation", "f")
    leg.AddEntry(None, "", "")
    leg.AddEntry(None, "bbA #rightarrow Zh", "")
    leg.AddEntry(Obs0sB,  "Observed", "l")
    leg.AddEntry(Exp0sB,  "Expected", "l")
    leg.SetY1(leg.GetY2()-leg.GetNRows()*0.045)
    leg.Draw()
    
    
#    latex = TLatex()
#    latex.SetNDC()
#    latex.SetTextSize(0.040)
#    latex.SetTextFont(42)
#    latex.DrawLatex(0.65, leg.GetY1()-0.045, "cos(#beta-#alpha)=0.25, tan(#beta)=1")

#    legB = TLegend(0.12, 0.4-4*0.3/5., 0.65, 0.4)
    legB = TLegend(0.15, 0.27, 0.68, 0.27)
    legB.SetBorderSize(0)
    legB.SetFillStyle(0) #1001
    legB.SetFillColor(0)
    for t in THEORY: legB.AddEntry(Theory[t], theoryLabel[t], "fl")
    legB.AddEntry(None, "cos(#beta-#alpha)=0.25, tan(#beta)=1", "")
    legB.SetY1(legB.GetY2()-legB.GetNRows()*0.045)
    legB.Draw()
    
    c1.GetPad(0).RedrawAxis()
    leg.Draw()

    c1.Update()
    
    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")

    c1.Print("plotsLimit/Exclusion/THDM.png")
    c1.Print("plotsLimit/Exclusion/THDM.pdf")



def limitCompare(method):
    signal, particle, particleP = "XVH", "V", "V'"

    channels = ["ah", "wrhpbb", "wrhpb", "wrlpbb", "wrlpb", "zrhpbb", "zrhpb", "zrlpbb", "zrlpb"]
    colors = [1, 610+4, 632, 800+7, 800, 416+1, 860+10, 600, 616, 921, 922]
    masses, vals, graphs = {}, {}, {}
    for j, c in enumerate(channels):
        masses[c], vals[c] = fillValues("./combine/" + method + "/"+signal+c+"_M%d.txt")
        graphs[c] = TGraph()
        n = 0
        #print vals[c]
        for i, m in enumerate(masses[c]):
            #if not signals[i] >= 1000: continue
            graphs[c].SetPoint(n, m, vals[c][m][3])
            n = n + 1
        graphs[c].SetLineColor(colors[j])
        graphs[c].SetLineWidth(3)
        graphs[c].Draw("SAME, L")

    c1 = TCanvas("c1", "Exclusion Limits", 800, 600)
    c1.cd()
    #SetPad(c1.GetPad(0))
    c1.GetPad(0).SetTopMargin(0.06)
    c1.GetPad(0).SetRightMargin(0.05)
    c1.GetPad(0).SetTicks(1, 1)
    c1.GetPad(0).SetLogy()
    for c in channels:
        graphs[c].Draw("AL" if 'ah' in c else "SAME, L")
    graphs[channels[0]].GetXaxis().SetRangeUser(SIGNALS[0], SIGNALS[-1])
    graphs[channels[0]].GetYaxis().SetRangeUser(0.25, 2.5e4)
    graphs[channels[0]].GetXaxis().SetTitle("m_{"+particleP+"} (GeV)")
    graphs[channels[0]].GetYaxis().SetTitle("#sigma("+particleP+") #bf{#it{#Beta}}("+particleP+" #rightarrow "+particle+"H) #bf{#it{#Beta}}(H #rightarrow bb) (fb)")
    drawAnalysis(signal)
    #drawRegion(signal, True)
    #drawCMS(LUMI, "Preliminary")
    drawCMS(LUMI, "Work in Progress", suppressCMS=True)

    # legend
    top = 0.9
    leg = TLegend(0.4, top-len(channels)*0.2/5., 0.99, top)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0) #1001
    leg.SetFillColor(0)
    leg.SetHeader("95% CL expected limits")
    for c in channels:
        leg.AddEntry(graphs[c],  getChannel(c), "l")
    leg.Draw()

    c1.Update()

    c1.Print("plotsLimit/Multi.png")
    c1.Print("plotsLimit/Multi.pdf")


if __name__ == "__main__":
    limit()
