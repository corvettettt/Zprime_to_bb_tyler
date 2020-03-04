#! /usr/bin/env python

###
### Macro for creating the datacards that are read by the combine tool.
###

print "starting package import"

import os, sys, getopt, multiprocessing
import copy, math, pickle
from array import array
from ROOT import gROOT, gSystem, gStyle, gRandom
from ROOT import TMath, TFile, TChain, TTree, TCut, TH1F, TH2F, TF1, THStack, TGraph, TGraphErrors, TGaxis
from ROOT import TStyle, TCanvas, TPad, TLegend, TLatex, TText

# Import PDF library
from ROOT import RooFit, RooRealVar, RooDataHist, RooDataSet, RooAbsData, RooAbsReal, RooAbsPdf, RooPlot, RooBinning, RooCategory, RooSimultaneous, RooArgList, RooArgSet, RooWorkspace, RooMsgService
from ROOT import RooFormulaVar, RooGenericPdf, RooGaussian, RooExponential, RooPolynomial, RooChebychev, RooBreitWigner, RooCBShape, RooExtendPdf, RooAddPdf

from rooUtils import *

import optparse

from samples import sample

print "packages imported"

usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage)
parser.add_option('-y', '--year', action='store', type='string', dest='year',default='2016')
parser.add_option("-c", "--category", action="store", type="string", dest="category", default="bb")
parser.add_option("-b", "--btagging", action="store", type="string", dest="btagging", default="medium")
(options, args) = parser.parse_args()
gROOT.SetBatch(True) #suppress immediate graphic output

########## SETTINGS ##########

BTAGGING    = options.btagging
CARDDIR     = "datacards/MANtag_study/"+BTAGGING+"/"
YEAR        = options.year
ISMC        = True
PLOTDIR     = "plots/MANtag_study/datacards/"
LUMI        = {'2016': 35920. , '2017': 41530., '2018': 59740., 'run2': 137190.}
if YEAR not in ['2016', '2017', '2018', 'run2']:
    print "unknown year:",YEAR
    sys.exit()

if BTAGGING not in ['tight', 'medium', 'loose', 'semimedium']:
    print "unknown btagging requirement:", BTAGGING
    sys.exit()

#categories = ['bb', 'bq']
categories = ['bb', 'bq', 'mumu']

massPoints = [x for x in range(1600, 8000+1, 100)]
genPoints = [1600, 1800, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000, 8000]

if not os.path.exists(PLOTDIR):
    os.makedirs(PLOTDIR)

def uncertainty_interpolation(year, category):

    uncerts = {'up':{}, 'down':{}}

    g_up = TGraph()
    g_up.SetTitle("uncert;m_{X} (GeV);uncert")
    g_up.SetMarkerStyle(20)
    g_up.SetMarkerColor(2)
    i_up = TGraph()
    i_up.SetMarkerStyle(24)
    i_up.SetMarkerColor(2)
    f_up = TF1("f_up", "pol0", 0, 1)
    g_down = TGraph()
    g_down.SetMarkerStyle(20)
    g_down.SetMarkerColor(4)
    i_down = TGraph()
    i_down.SetMarkerStyle(24)
    i_down.SetMarkerColor(4)
    f_down = TF1("f_down", "pol0", 0, 1)

    n=0
    for i, m in enumerate(genPoints):
        if year=="run2":
            up_value = 0
            for yr in ['2016', '2017', '2018']:
                up_value += LUMI[yr]*sample['ZpBB_M{}'.format(m)]['BTag_uncertainties'][yr]['up'][category]
            up_value /= LUMI['run2'] 
        else: 
            up_value = sample['ZpBB_M{}'.format(m)]['BTag_uncertainties'][year]['up'][category]
        if up_value==-100: continue
        g_up.SetPoint(n, m, up_value)
        n = n + 1
    if n==0:
        print "no valid uncertainties detected!!"
        sys.exit()
    n=0
    for i, m in enumerate(genPoints):
        if year=="run2":
            down_value = 0
            for yr in ['2016', '2017', '2018']:
                down_value += LUMI[yr]*sample['ZpBB_M{}'.format(m)]['BTag_uncertainties'][yr]['down'][category]
            down_value /= LUMI['run2'] 
        else: 
            down_value = sample['ZpBB_M{}'.format(m)]['BTag_uncertainties'][year]['down'][category]
        if down_value==-100: continue
        g_down.SetPoint(n, m, down_value)
        n = n + 1
    if n==0:
        print "no valid uncertainties detected!!"
        sys.exit()

    g_up.Fit(f_up, "Q0", "SAME")
    g_down.Fit(f_down, "Q0", "SAME")
    
    for m in massPoints:
        up_val = g_up.Eval(m)
        uncerts['up'][m] = up_val
        i_up.SetPoint(i_up.GetN(), m, up_val)
        down_val = g_down.Eval(m)
        uncerts['down'][m] = down_val
        i_down.SetPoint(i_down.GetN(), m, down_val)
    
    c = TCanvas("c2", "Signal Efficiency", 800, 600)
    g_up.Draw("APL")
    i_up.Draw("P, SAME")
    g_down.Draw("PL, SAME")
    i_down.Draw("P, SAME")
    g_up.GetYaxis().SetRangeUser(-0.25,0.25)
    g_up.GetXaxis().SetRangeUser(genPoints[0]-100, genPoints[-1]+100)
    
    leg = TLegend(0.7, 0.75, 0.9, 0.9)
    leg.AddEntry(g_up, "up")
    leg.AddEntry(g_down, "down")
    leg.Draw()
    c.Print(PLOTDIR+"uncertainty_interpol_{}_{}.png".format(year, category))
   
    return uncerts 


######## syst uncert #########

syst_sig = {}
syst_sig["lnN"] = {}
syst_sig["param"] = {}

syst_sig["lnN"]["lumi"] = 0.026
syst_sig["param"]["CMS"+YEAR+"sig_p1_jes"] = (0., 1.)
syst_sig["param"]["CMS"+YEAR+"sig_p2_jer"] = (0., 1.)

# linear interpolation of btagging uncertainties:
syst_sig["BTag"] = {}
for category in categories:
    syst_sig["BTag"][category] = uncertainty_interpolation(YEAR, category)

##############################

def datacards(category):

    for i, m in enumerate(massPoints):
        generate_datacard(YEAR, category, m, BTAGGING, CARDDIR+"%s_%s_M%d%s.txt" % (category, YEAR, m, "_MC" if ISMC else ""))


def generate_datacard(year, category, masspoint, btagging, outname):
    signalName = "ZpBB_{}_{}_M{}".format(year, category, masspoint)
    backgroundName = "Bkg_{}_{}".format(year, category)
    card  = "imax 1\n"
    card += "jmax 1\n"
    card += "kmax *\n"
    card += "-----------------------------------------------------------------------------------\n"
    card += "shapes         {sname}  *    workspace/MANtag_study/{btagging}/MC_signal_{year}_{category}.root     Zprime_{year}:{sname}\n".format(sname=signalName, year=year, category=category, btagging=btagging)
    card += "shapes         {bname}  *    workspace/MANtag_study/{btagging}/{data_type}_{year}_{category}.root    Zprime_{year}:{bname}\n".format(bname=backgroundName, data_type="MC_QCD_TTbar" if ISMC else "data", year=year, category=category, btagging=btagging)
    card += "shapes         data_obs  *    workspace/MANtag_study/{btagging}/{data_type}_{year}_{category}.root    Zprime_{year}:data_obs\n".format(data_type="MC_QCD_TTbar" if ISMC else "data", year=year, category=category, btagging=btagging)
    card += "-----------------------------------------------------------------------------------\n"
    card += "bin                              {}\n".format(category)
    card += "observation                      -1\n"
    card += "-----------------------------------------------------------------------------------\n"
    card += "bin                              {:25}{:25}\n".format(category, category)
    card += "process                          {:25}{:25}\n".format(signalName, backgroundName) 
    card += "process                          {:25}{:25}\n".format("0", "1")
    card += "rate                             {:25}{:25}\n".format("1", "1") 
    card += "-----------------------------------------------------------------------------------\n"
    #simple uncertainties (currently only lumi)
    for syst_unc in sorted(syst_sig["lnN"].keys()):
        card += "{:<25}{:<6}  {:<25}{:<25}\n".format(syst_unc, 'lnN', 1+syst_sig["lnN"][syst_unc], '-')
    #JES and JER
    for syst_unc in sorted(syst_sig["param"].keys()):
        card += "{:<25}{:<6}  {:<25}{:<25}\n".format(syst_unc.replace('sig_', 'sig_'+category+'_'), 'param', syst_sig["param"][syst_unc][0], syst_sig["param"][syst_unc][1])
   
    cardfile = open(outname, 'w')
    cardfile.write(card)
    cardfile.close()
    print "Datacards for mass", masspoint, "in category", category, "saved in", outname



if __name__ == "__main__":
    datacards(options.category)
    #else:
    #    jobs=[]
    #    for c in categories:
    #        p = multiprocessing.Process(target=datacards, args=(c,))
    #        jobs.append(p)
    #        p.start()


