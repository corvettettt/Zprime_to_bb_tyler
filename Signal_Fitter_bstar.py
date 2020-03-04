#!/usr/bin/env python

###
### Macro used for fitting the MC signal and saving the fits as a rooWorkspace for use by combine.
###

import global_paths
import os, sys, getopt, multiprocessing
import copy, math, pickle
from array import array

from ROOT import gROOT, gSystem, gStyle, gRandom
from ROOT import TMath, TFile, TChain, TTree, TCut, TH1F, TH2F, THStack, TGraph, TGaxis
from ROOT import TStyle, TCanvas, TPad, TLegend, TLatex, TText, TColor
from ROOT import TH1, TF1, TGraph, TGraphErrors, TGraphAsymmErrors, TVirtualFitter

gSystem.Load("PDFs/HWWLVJRooPdfs_cxx.so") #needed to get the DoubleCrytalBall pdf
from ROOT import RooFit, RooRealVar, RooDataHist, RooDataSet, RooAbsData, RooAbsReal, RooAbsPdf, RooPlot, RooBinning, RooCategory, RooSimultaneous, RooArgList, RooArgSet, RooWorkspace, RooMsgService
from ROOT import RooFormulaVar, RooGenericPdf, RooGaussian, RooExponential, RooPolynomial, RooChebychev, RooBreitWigner, RooCBShape, RooExtendPdf, RooAddPdf, RooDoubleCrystalBall

#from alpha import drawPlot
from rooUtils import *
from samples_bstar import sample
from aliases_bstar import alias, aliasSM, working_points, dijet_bins
from aliases_bstar import additional_selections as SELECTIONS
from utils import extend_binning

import optparse

usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage)

parser.add_option("-v", "--verbose", action="store_true", default=False, dest="verbose")
parser.add_option("-y", "--year", action="store", type="string", dest="year",default="2017")
parser.add_option("-c", "--category", action="store", type="string", dest="category", default="")
parser.add_option("-b", "--btagging", action="store", type="string", dest="btagging", default="medium")
parser.add_option("-u", "--unskimmed", action="store_true", default=False, dest="unskimmed")
parser.add_option("-s", "--selection", action="store", type="string", dest="selection", default="")
(options, args) = parser.parse_args()
gROOT.SetBatch(True)

colour = [
    TColor(1001, 0., 0., 0., "black", 1.),
    TColor(1002, 230./255, 159./255, 0., "orange", 1.),
    TColor(1003, 86./255, 180./255, 233./255, "skyblue", 1.),
    TColor(1004, 0., 158./255, 115./255, "bluishgreen", 1.),
    TColor(1005, 0., 114./255, 178./255, "blue", 1.),
    TColor(1006, 213./255, 94./255, 0., "vermillion", 1.),
    TColor(1007, 204./255, 121./255, 167./255, "reddishpurple", 1.),
]

########## SETTINGS ##########

channel = 'bb'
stype = 'Zprime' 
genPoints= [500]+range(1000,10000,1000)
#genPoints = [1600, 1800, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000, 8000]
massPoints = [500,1000]+[x for x in range(1600, 8000+1, 100)]

# Silent RooFit
RooMsgService.instance().setGlobalKillBelow(RooFit.FATAL)

gStyle.SetOptTitle(0)
gStyle.SetPadTopMargin(0.06)
gStyle.SetPadRightMargin(0.05)
gStyle.SetPadLeftMargin(0.12)
gStyle.SetErrorX(0.)

BTAGGING    = options.btagging
NTUPLEDIR   = global_paths.SKIMMEDDIR
PLOTDIR     = "plots/"+BTAGGING+"/"
WORKDIR     = "workspace/"+BTAGGING+"/" 
RATIO       = 4
YEAR        = options.year
VERBOSE     = options.verbose
READTREE    = True
ADDSELECTION= options.selection!=""
VARBINS     = True

X_MIN = 130.
X_MAX = 9067.
#X_MIN = 1800.
#X_MAX = 9000.

if YEAR=='2016':
    LUMI=35920.
elif YEAR=='2017':
    LUMI=41530.
elif YEAR=='2018':
    LUMI=59740.
elif YEAR=='run2':
    LUMI=137190.
else:
    print "unknown year:",YEAR
    sys.exit()

if BTAGGING not in ['tight', 'medium', 'loose', 'semimedium']:
    print "unknown btagging requirement:", BTAGGING
    sys.exit()

if options.unskimmed:
    NTUPLEDIR=global_paths.WEIGHTEDDIR

if options.selection not in SELECTIONS.keys():
    print "invalid selection!"
    sys.exit()

channelList = ['bb']
signalList = ['Zprbb']
color = {'bb' : 4, 'bq': 2, 'qq': 8, 'mumu': 6}
channel = 'bb'
categories = ['bb', 'bq', 'mumu']
stype = 'Zprime' 
signalType = 'Zprime'

jobs = []

if VARBINS:
    bins = [x for x in dijet_bins if x>=X_MIN and x<=X_MAX]
    X_min = min(bins)
    X_max = max(bins)
    narrow_bins = extend_binning(10, bins)
    abins = array( 'd', narrow_bins )
    print "dijet bins:", bins
    print "narrow bins:", narrow_bins
else:
    X_min = X_MIN-X_MIN%10
    X_max = X_MAX-(X_MAX-X_min)%100
    print "X_min =",X_min
    print "X_max =",X_max


def signal(category):

    interPar = True
    n = len(genPoints)  
    
    cColor = color[category] if category in color else 4
    nBtag = category.count('b')
    isAH = False #relict from using Alberto's more complex script 
 
    if not os.path.exists(PLOTDIR+"MC_signal_"+YEAR): os.makedirs(PLOTDIR+"MC_signal_"+YEAR)

    #*******************************************************#
    #                                                       #
    #              Variables and selections                 #
    #                                                       #
    #*******************************************************#

    X_mass  = RooRealVar (      "jj_mass_widejet",              "m_{jj}",       X_min,     X_max,  "GeV")
    j1_pt = RooRealVar(         "jpt_1",                "jet1 pt",      0.,     13000.,  "GeV")
    jj_deltaEta = RooRealVar(    "jj_deltaEta_widejet",                "",      0.,     5.)
    jbtag_WP_1 = RooRealVar("jbtag_WP_1",       "",             -1.,   4.        )
    jbtag_WP_2 = RooRealVar("jbtag_WP_2",       "",             -1.,   4.        )
    fatjetmass_1 = RooRealVar("fatjetmass_1",   "",             -1.,   2500.     )
    fatjetmass_2 = RooRealVar("fatjetmass_2",   "",             -1.,   2500.     )
    jid_1 = RooRealVar(   "jid_1",      "j1 ID",    -1.,   8.)
    jid_2 = RooRealVar(   "jid_2",      "j2 ID",    -1.,   8.)
    jnmuons_1 = RooRealVar(   "jnmuons_1",      "j1 n_{#mu}",    -1.,   8.)
    jnmuons_2 = RooRealVar(   "jnmuons_2",      "j2 n_{#mu}",    -1.,   8.)
    jmuonpt_1 = RooRealVar(   "jmuonpt_1",      "j1 muon pt",    0.,   13000.)
    jmuonpt_2 = RooRealVar(   "jmuonpt_2",      "j2 muon pt",    0.,   13000.)
    nmuons = RooRealVar(    "nmuons",       "n_{#mu}",          -1.,   10.     )
    nelectrons = RooRealVar("nelectrons",    "n_{e}",            -1.,   10.     )
    HLT_AK8PFJet500         = RooRealVar("HLT_AK8PFJet500"         , "",  -1., 1.    )
    HLT_PFJet500            = RooRealVar("HLT_PFJet500"            , "" , -1., 1.    ) 
    HLT_CaloJet500_NoJetID  = RooRealVar("HLT_CaloJet500_NoJetID"  , "" , -1., 1.    ) 
    HLT_PFHT900             = RooRealVar("HLT_PFHT900"            , "" , -1., 1.    ) 
    HLT_AK8PFJet550         = RooRealVar("HLT_AK8PFJet550"         , "",  -1., 1.    )
    HLT_PFJet550            = RooRealVar("HLT_PFJet550"            , "" , -1., 1.    ) 
    HLT_CaloJet550_NoJetID  = RooRealVar("HLT_CaloJet550_NoJetID"  , "" , -1., 1.    ) 
    HLT_PFHT1050            = RooRealVar("HLT_PFHT1050"            , "" , -1., 1.    ) 
    HLT_DoublePFJets100_CaloBTagDeepCSV_p71                 =RooRealVar("HLT_DoublePFJets100_CaloBTagDeepCSV_p71"                , "", -1., 1. ) 
    HLT_DoublePFJets116MaxDeta1p6_DoubleCaloBTagDeepCSV_p71 =RooRealVar("HLT_DoublePFJets116MaxDeta1p6_DoubleCaloBTagDeepCSV_p71", "", -1., 1. ) 
    HLT_DoublePFJets128MaxDeta1p6_DoubleCaloBTagDeepCSV_p71 =RooRealVar("HLT_DoublePFJets128MaxDeta1p6_DoubleCaloBTagDeepCSV_p71", "", -1., 1. ) 
    HLT_DoublePFJets200_CaloBTagDeepCSV_p71                 =RooRealVar("HLT_DoublePFJets200_CaloBTagDeepCSV_p71"                , "", -1., 1. ) 
    HLT_DoublePFJets350_CaloBTagDeepCSV_p71                 =RooRealVar("HLT_DoublePFJets350_CaloBTagDeepCSV_p71"                , "", -1., 1. ) 
    HLT_DoublePFJets40_CaloBTagDeepCSV_p71                  =RooRealVar("HLT_DoublePFJets40_CaloBTagDeepCSV_p71"                 , "", -1., 1. )

    weight = RooRealVar(        "eventWeightLumi",      "",             -1.e9,  1.e9    )

    # Define the RooArgSet which will include all the variables defined before
    # there is a maximum of 9 variables in the declaration, so the others need to be added with 'add'
    variables = RooArgSet(X_mass)
    variables.add(RooArgSet(j1_pt, jj_deltaEta, jbtag_WP_1, jbtag_WP_2, fatjetmass_1, fatjetmass_2, jnmuons_1, jnmuons_2, weight))
    variables.add(RooArgSet(nmuons, nelectrons, jid_1, jid_2, jmuonpt_1, jmuonpt_2))
    variables.add(RooArgSet(HLT_AK8PFJet500, HLT_PFJet500, HLT_CaloJet500_NoJetID, HLT_PFHT900, HLT_AK8PFJet550, HLT_PFJet550, HLT_CaloJet550_NoJetID, HLT_PFHT1050))
    variables.add(RooArgSet(HLT_DoublePFJets100_CaloBTagDeepCSV_p71, HLT_DoublePFJets116MaxDeta1p6_DoubleCaloBTagDeepCSV_p71, HLT_DoublePFJets128MaxDeta1p6_DoubleCaloBTagDeepCSV_p71, HLT_DoublePFJets200_CaloBTagDeepCSV_p71, HLT_DoublePFJets350_CaloBTagDeepCSV_p71, HLT_DoublePFJets40_CaloBTagDeepCSV_p71))
    X_mass.setRange("X_reasonable_range", X_mass.getMin(), X_mass.getMax())
    X_mass.setRange("X_integration_range", X_mass.getMin(), X_mass.getMax())

    if VARBINS:        
        binsXmass = RooBinning(len(abins)-1, abins)
        X_mass.setBinning(binsXmass)
        plot_binning = RooBinning(int((X_mass.getMax()-X_mass.getMin())/100), X_mass.getMin(), X_mass.getMax())
    else:
        X_mass.setBins(int((X_mass.getMax()-X_mass.getMin())/10))
        binsXmass = RooBinning(int((X_mass.getMax()-X_mass.getMin())/100), X_mass.getMin(), X_mass.getMax())
        plot_binning = binsXmass

    X_mass.setBinning(plot_binning, "PLOT")

    #X_mass.setBins(int((X_mass.getMax() - X_mass.getMin())/10))
    #binsXmass = RooBinning(int((X_mass.getMax() - X_mass.getMin())/100), X_mass.getMin(), X_mass.getMax())
    #X_mass.setBinning(binsXmass, "PLOT")
    massArg = RooArgSet(X_mass)

    # Cuts
    if BTAGGING=='semimedium':
        SRcut = aliasSM[category]
        #SRcut = aliasSM[category+"_vetoAK8"]
    else:
        SRcut = alias[category].format(WP=working_points[BTAGGING])
        #SRcut = alias[category+"_vetoAK8"].format(WP=working_points[BTAGGING])

    if ADDSELECTION: SRcut += SELECTIONS[options.selection]

    print "  Cut:\t", SRcut

    #*******************************************************#
    #                                                       #
    #                    Signal fits                        #
    #                                                       #
    #*******************************************************#

    treeSign = {}
    setSignal = {}

    vmean  = {}
    vsigma = {}
    valpha1 = {}
    vslope1 = {}
    valpha2 = {}
    vslope2 = {}
    smean  = {}
    ssigma = {}
    salpha1 = {}
    sslope1 = {}
    salpha2 = {}
    sslope2 = {}
    sbrwig = {}
    signal = {}
    signalExt = {}
    signalYield = {}
    signalIntegral = {}
    signalNorm = {}
    signalXS = {}
    frSignal = {}
    frSignal1 = {}
    frSignal2 = {}
    frSignal3 = {}

    # Signal shape uncertainties (common amongst all mass points) 
    xmean_jes = RooRealVar("CMS"+YEAR+"_sig_"+category+"_p1_scale_jes", "Variation of the resonance position with the jet energy scale", 0.02, -1., 1.) #0.001
    smean_jes = RooRealVar("CMS"+YEAR+"_sig_"+category+"_p1_jes", "Change of the resonance position with the jet energy scale", 0., -10, 10)

    xsigma_jer = RooRealVar("CMS"+YEAR+"_sig_"+category+"_p2_scale_jer", "Variation of the resonance width with the jet energy resolution", 0.10, -1., 1.)
    ssigma_jer = RooRealVar("CMS"+YEAR+"_sig_"+category+"_p2_jer", "Change of the resonance width with the jet energy resolution", 0., -10, 10)
    
    xmean_jes.setConstant(True)
    smean_jes.setConstant(True)
    
    xsigma_jer.setConstant(True)
    ssigma_jer.setConstant(True)
    
    for m in massPoints:

        signalMass = "%s_M%d" % (stype, m)
        signalName = "ZpBB_{}_{}_M{}".format(YEAR, category, m)
        sampleName = "bstar_M{}".format(m)
 
        signalColor = sample[sampleName]['linecolor'] if signalName in sample else 1

        # define the signal PDF
        vmean[m] = RooRealVar(signalName + "_vmean", "Crystal Ball mean", m, m*0.96, m*1.05)
        smean[m] = RooFormulaVar(signalName + "_mean", "@0*(1+@1*@2)", RooArgList(vmean[m], xmean_jes, smean_jes))

        vsigma[m] = RooRealVar(signalName + "_vsigma", "Crystal Ball sigma", m*0.0233, m*0.019, m*0.025)
        ssigma[m] = RooFormulaVar(signalName + "_sigma", "@0*(1+@1*@2)", RooArgList(vsigma[m], xsigma_jer, ssigma_jer))
 
        valpha1[m] = RooRealVar(signalName + "_valpha1", "Crystal Ball alpha 1", 0.2,  0.05, 0.28) # number of sigmas where the exp is attached to the gaussian core. >0 left, <0 right
        salpha1[m] = RooFormulaVar(signalName + "_alpha1", "@0", RooArgList(valpha1[m]))

        #vslope1[m] = RooRealVar(signalName + "_vslope1", "Crystal Ball slope 1", 10., 0.1, 20.) # slope of the power tail
        vslope1[m] = RooRealVar(signalName + "_vslope1", "Crystal Ball slope 1", 13., 10., 20.) # slope of the power tail
        sslope1[m] = RooFormulaVar(signalName + "_slope1", "@0", RooArgList(vslope1[m]))
        

        valpha2[m] = RooRealVar(signalName + "_valpha2", "Crystal Ball alpha 2", 1.)
        valpha2[m].setConstant(True)
        salpha2[m] = RooFormulaVar(signalName + "_alpha2", "@0", RooArgList(valpha2[m]))

        #vslope2[m] = RooRealVar(signalName + "_vslope2", "Crystal Ball slope 2", 6., 2.5, 15.) # slope of the higher power tail
        ## FIXME test FIXME
        vslope2_estimation = -5.88111436852 + m*0.00728809389442 + m*m*(-1.65059568762e-06) + m*m*m*(1.25128996309e-10)
        vslope2[m] = RooRealVar(signalName + "_vslope2", "Crystal Ball slope 2", vslope2_estimation, vslope2_estimation*0.9, vslope2_estimation*1.1) # slope of the higher power tail
        ## FIXME end FIXME
        sslope2[m] = RooFormulaVar(signalName + "_slope2", "@0", RooArgList(vslope2[m])) # slope of the higher power tail

        signal[m] = RooDoubleCrystalBall(signalName, "m_{%s'} = %d GeV" % ('X', m), X_mass, smean[m], ssigma[m], salpha1[m], sslope1[m], salpha2[m], sslope2[m])

        # extend the PDF with the yield to perform an extended likelihood fit
        signalYield[m] = RooRealVar(signalName+"_yield", "signalYield", 50, 0., 1.e15)
        signalNorm[m] = RooRealVar(signalName+"_norm", "signalNorm", 1., 0., 1.e15)
        signalXS[m] = RooRealVar(signalName+"_xs", "signalXS", 1., 0., 1.e15)
        signalExt[m] = RooExtendPdf(signalName+"_ext", "extended p.d.f", signal[m], signalYield[m])

        # ---------- if there is no simulated signal, skip this mass point ----------
        if m in genPoints:
            if VERBOSE: print " - Mass point", m

            # define the dataset for the signal applying the SR cuts
            treeSign[m] = TChain("tree")

            if YEAR=='run2':
                pd = sample[sampleName]['files']
                if len(pd)>3:
                    print "multiple files given than years for a single masspoint:",pd
                    sys.exit()
                for ss in pd:
                    if not '2016' in ss and not '2017' in ss and not '2018' in ss:
                        print "unknown year given in:", ss
                        sys.exit()
            else:
                pd = [x for x in sample[sampleName]['files'] if YEAR in x]
                if len(pd)>1:
                    print "multiple files given for a single masspoint/year:",pd
                    sys.exit()
            
            for ss in pd:

                if options.unskimmed:
                    j=0
                    while True:
                        if os.path.exists(NTUPLEDIR + ss + "/" + ss + "_flatTuple_{}.root".format(j)):
                            treeSign[m].Add(NTUPLEDIR + ss + "/" + ss + "_flatTuple_{}.root".format(j))
                            j += 1
                        else:
                            print "found {} files for sample:".format(j), ss
                            break
                else:
                    if os.path.exists(NTUPLEDIR + ss + ".root"):
                        treeSign[m].Add(NTUPLEDIR + ss + ".root")
                    else:
                        print "found no file for sample:", ss
            
            if treeSign[m].GetEntries() <= 0.:
                if VERBOSE: print " - 0 events available for mass", m, "skipping mass point..."
                signalNorm[m].setVal(-1)
                vmean[m].setConstant(True)
                vsigma[m].setConstant(True)
                salpha1[m].setConstant(True)
                sslope1[m].setConstant(True)
                salpha2[m].setConstant(True)
                sslope2[m].setConstant(True)
                signalNorm[m].setConstant(True)
                signalXS[m].setConstant(True)
                continue
            
            #setSignal[m] = RooDataSet("setSignal_"+signalName, "setSignal", variables, RooFit.Cut(SRcut), RooFit.WeightVar("eventWeightLumi*BTagAK4Weight_deepJet"), RooFit.Import(treeSign[m]))
            setSignal[m] = RooDataSet("setSignal_"+signalName, "setSignal", variables, RooFit.Cut(SRcut), RooFit.WeightVar(weight), RooFit.Import(treeSign[m]))
            if VERBOSE: print " - Dataset with", setSignal[m].sumEntries(), "events loaded"
           
            # FIT
            entries = setSignal[m].sumEntries()
            if entries < 0. or entries != entries: entries = 0
            signalYield[m].setVal(entries)
            # Instead of eventWeightLumi
            #signalYield[m].setVal(entries * LUMI / (300000 if YEAR=='run2' else 100000) )

            if treeSign[m].GetEntries(SRcut) > 5:
                if VERBOSE: print " - Running fit"
                frSignal[m] = signalExt[m].fitTo(setSignal[m], RooFit.Save(1), RooFit.Extended(True), RooFit.SumW2Error(True), RooFit.PrintLevel(-1))
                if VERBOSE: print "********** Fit result [", m, "] **", category, "*"*40, "\n", frSignal[m].Print(), "\n", "*"*80
                if VERBOSE: frSignal[m].correlationMatrix().Print()
                drawPlot(signalMass+"_"+category, stype+category, X_mass, signal[m], setSignal[m], frSignal[m])
 
            else:
                print "  WARNING: signal", stype, "and mass point", m, "in category", category, "has 0 entries or does not exist"
                        
            # Remove HVT cross sections
            #xs = getCrossSection(stype, channel, m)
            xs = 1.    
            signalXS[m].setVal(xs * 1000.)
            
            signalIntegral[m] = signalExt[m].createIntegral(massArg, RooFit.NormSet(massArg), RooFit.Range("X_integration_range"))
            boundaryFactor = signalIntegral[m].getVal()
            if boundaryFactor < 0. or boundaryFactor != boundaryFactor: boundaryFactor = 0
            if VERBOSE: print " - Fit normalization vs integral:", signalYield[m].getVal(), "/", boundaryFactor, "events"
            signalNorm[m].setVal( boundaryFactor * signalYield[m].getVal() / signalXS[m].getVal()) # here normalize to sigma(X) x Br = 1 [fb]
            
        vmean[m].setConstant(True)
        vsigma[m].setConstant(True)
        valpha1[m].setConstant(True)
        vslope1[m].setConstant(True)
        valpha2[m].setConstant(True)
        vslope2[m].setConstant(True)
        signalNorm[m].setConstant(True)
        signalXS[m].setConstant(True)
        

    #*******************************************************#
    #                                                       #
    #                 Signal interpolation                  #
    #                                                       #
    #*******************************************************#

    ### FIXME FIXME just for a test FIXME FIXME

    #print
    #print
    #print "slope2 fit results:"
    #print 
    #y_vals = []
    #for m in genPoints:
    #    y_vals.append(vslope2[m].getVal())
    #print "m =", genPoints
    #print "y =", y_vals
    #sys.exit()

    ### FIXME FIXME test end FIXME FIXME


    # ====== CONTROL PLOT ======
    color_scheme = [636, 635, 634, 633, 632, 633, 636, 635, 634, 633, 632, 633, 636, 635, 634, 633, 632, 633, 636, 635, 634, 633, 632, 633, 636, 635, 634, 633, 632, 633, 636, 635, 634, 633, 632, 633, 636, 635, 634, 633, 632, 633]
    c_signal = TCanvas("c_signal", "c_signal", 800, 600)
    c_signal.cd()
    frame_signal = X_mass.frame()
    for j, m in enumerate(genPoints):
        if m in signalExt.keys():
            #print "color:",(j%9)+1
            #print "signalNorm[m].getVal() =", signalNorm[m].getVal()
            #print "RooAbsReal.NumEvent =", RooAbsReal.NumEvent
            signal[m].plotOn(frame_signal, RooFit.LineColor(color_scheme[j]), RooFit.Normalization(signalNorm[m].getVal(), RooAbsReal.NumEvent), RooFit.Range("X_reasonable_range"))
    frame_signal.GetXaxis().SetRangeUser(0, 10000)
    frame_signal.Draw()
    #drawCMS(-1, "Simulation Preliminary", year=YEAR)
    #drawCMS(-1, "Work in Progress", year=YEAR, suppressCMS=True)
    drawCMS(-1, "", year=YEAR, suppressCMS=True)
    drawAnalysis(category)
    drawRegion(category)

    c_signal.SaveAs(PLOTDIR+"MC_bstar_"+YEAR+"/"+stype+"_"+category+"_Signal.pdf")
    c_signal.SaveAs(PLOTDIR+"MC_bstar_"+YEAR+"/"+stype+"_"+category+"_Signal.png")
    #if VERBOSE: raw_input("Press Enter to continue...")
    # ====== CONTROL PLOT ======

    # Normalization
    gnorm = TGraphErrors()
    gnorm.SetTitle(";m_{X} (GeV);integral (GeV)")
    gnorm.SetMarkerStyle(20)
    gnorm.SetMarkerColor(1)
    gnorm.SetMaximum(0)
    inorm = TGraphErrors()
    inorm.SetMarkerStyle(24)
    fnorm = TF1("fnorm", "pol9", 700, 3000) 
    fnorm.SetLineColor(920)
    fnorm.SetLineStyle(7)
    fnorm.SetFillColor(2)
    fnorm.SetLineColor(cColor)

    # Mean
    gmean = TGraphErrors()
    gmean.SetTitle(";m_{X} (GeV);gaussian mean (GeV)")
    gmean.SetMarkerStyle(20)
    gmean.SetMarkerColor(cColor)
    gmean.SetLineColor(cColor)
    imean = TGraphErrors()
    imean.SetMarkerStyle(24)
    fmean = TF1("fmean", "pol1", 0, 10000)
    fmean.SetLineColor(2)
    fmean.SetFillColor(2)

    # Width
    gsigma = TGraphErrors()
    gsigma.SetTitle(";m_{X} (GeV);gaussian width (GeV)")
    gsigma.SetMarkerStyle(20)
    gsigma.SetMarkerColor(cColor)
    gsigma.SetLineColor(cColor)
    isigma = TGraphErrors()
    isigma.SetMarkerStyle(24)
    fsigma = TF1("fsigma", "pol1", 0, 10000)
    fsigma.SetLineColor(2)
    fsigma.SetFillColor(2)

    # Alpha1
    galpha1 = TGraphErrors()
    galpha1.SetTitle(";m_{X} (GeV);crystal ball lower alpha")
    galpha1.SetMarkerStyle(20)
    galpha1.SetMarkerColor(cColor)
    galpha1.SetLineColor(cColor)
    ialpha1 = TGraphErrors()
    ialpha1.SetMarkerStyle(24)
    falpha1 = TF1("falpha", "pol1", 0, 10000) #pol0
    falpha1.SetLineColor(2)
    falpha1.SetFillColor(2)

    # Slope1
    gslope1 = TGraphErrors()
    gslope1.SetTitle(";m_{X} (GeV);exponential lower slope (1/Gev)")
    gslope1.SetMarkerStyle(20)
    gslope1.SetMarkerColor(cColor)
    gslope1.SetLineColor(cColor)
    islope1 = TGraphErrors()
    islope1.SetMarkerStyle(24)
    fslope1 = TF1("fslope", "pol1", 0, 10000) #pol0
    fslope1.SetLineColor(2)
    fslope1.SetFillColor(2)

    # Alpha2
    galpha2 = TGraphErrors()
    galpha2.SetTitle(";m_{X} (GeV);crystal ball upper alpha")
    galpha2.SetMarkerStyle(20)
    galpha2.SetMarkerColor(cColor)
    galpha2.SetLineColor(cColor)
    ialpha2 = TGraphErrors()
    ialpha2.SetMarkerStyle(24)
    falpha2 = TF1("falpha", "pol1", 0, 10000) #pol0
    falpha2.SetLineColor(2)
    falpha2.SetFillColor(2)

    # Slope2
    gslope2 = TGraphErrors()
    gslope2.SetTitle(";m_{X} (GeV);exponential upper slope (1/Gev)")
    gslope2.SetMarkerStyle(20)
    gslope2.SetMarkerColor(cColor)
    gslope2.SetLineColor(cColor)
    islope2 = TGraphErrors()
    islope2.SetMarkerStyle(24)
    fslope2 = TF1("fslope", "pol1", 0, 10000) #pol0
    fslope2.SetLineColor(2)
    fslope2.SetFillColor(2)


    n = 0
    for i, m in enumerate(genPoints):
        if not m in signalNorm.keys(): continue
        if signalNorm[m].getVal() < 1.e-6: continue

        if gnorm.GetMaximum() < signalNorm[m].getVal(): gnorm.SetMaximum(signalNorm[m].getVal())
        gnorm.SetPoint(n, m, signalNorm[m].getVal())
        #gnorm.SetPointError(i, 0, signalNorm[m].getVal()/math.sqrt(treeSign[m].GetEntriesFast()))
        gmean.SetPoint(n, m, vmean[m].getVal())
        gmean.SetPointError(n, 0, min(vmean[m].getError(), vmean[m].getVal()*0.02))
        gsigma.SetPoint(n, m, vsigma[m].getVal())
        gsigma.SetPointError(n, 0, min(vsigma[m].getError(), vsigma[m].getVal()*0.05))
        galpha1.SetPoint(n, m, valpha1[m].getVal())
        galpha1.SetPointError(n, 0, min(valpha1[m].getError(), valpha1[m].getVal()*0.10))
        gslope1.SetPoint(n, m, vslope1[m].getVal())
        gslope1.SetPointError(n, 0, min(vslope1[m].getError(), vslope1[m].getVal()*0.10))
        galpha2.SetPoint(n, m, salpha2[m].getVal())
        galpha2.SetPointError(n, 0, min(valpha2[m].getError(), valpha2[m].getVal()*0.10))
        gslope2.SetPoint(n, m, sslope2[m].getVal())
        gslope2.SetPointError(n, 0, min(vslope2[m].getError(), vslope2[m].getVal()*0.10))
        #tmpVar = w.var(var+"_"+signalString)
        #print m, tmpVar.getVal(), tmpVar.getError()
        n = n + 1

    gmean.Fit(fmean, "Q0", "SAME")
    gsigma.Fit(fsigma, "Q0", "SAME")
    galpha1.Fit(falpha1, "Q0", "SAME")
    gslope1.Fit(fslope1, "Q0", "SAME")
    galpha2.Fit(falpha2, "Q0", "SAME")
    gslope2.Fit(fslope2, "Q0", "SAME")
#    gnorm.Fit(fnorm, "Q0", "", 700, 5000)
    #for m in [5000, 5500]: gnorm.SetPoint(gnorm.GetN(), m, gnorm.Eval(m, 0, "S"))
    #gnorm.Fit(fnorm, "Q", "SAME", 700, 6000)
    gnorm.Fit(fnorm, "Q", "SAME", 1800, 8000) ## adjusted recently

    for m in massPoints:

        if vsigma[m].getVal() < 10.: vsigma[m].setVal(10.)

        # Interpolation method
        syield = gnorm.Eval(m)
        spline = gnorm.Eval(m, 0, "S")
        sfunct = fnorm.Eval(m)
        
        #delta = min(abs(1.-spline/sfunct), abs(1.-spline/syield))
        delta = abs(1.-spline/sfunct) if sfunct > 0 else 0
        syield = spline
        
        if interPar:
            #jmean = gmean.Eval(m)
            #jsigma = gsigma.Eval(m)
            #jalpha1 = galpha1.Eval(m)
            #jslope1 = gslope1.Eval(m)
            #jalpha2 = galpha2.Eval(m)
            #jslope2 = gslope2.Eval(m)
            jmean = gmean.Eval(m, 0, "S") 
            jsigma = gsigma.Eval(m, 0, "S")
            jalpha1 = galpha1.Eval(m, 0, "S")
            jslope1 = gslope1.Eval(m, 0, "S")
            jalpha2 = galpha2.Eval(m, 0, "S")
            jslope2 = gslope2.Eval(m, 0, "S")

        else:
            jmean = fmean.GetParameter(0) + fmean.GetParameter(1)*m + fmean.GetParameter(2)*m*m
            jsigma = fsigma.GetParameter(0) + fsigma.GetParameter(1)*m + fsigma.GetParameter(2)*m*m
            jalpha1 = falpha1.GetParameter(0) + falpha1.GetParameter(1)*m + falpha1.GetParameter(2)*m*m
            jslope1 = fslope1.GetParameter(0) + fslope1.GetParameter(1)*m + fslope1.GetParameter(2)*m*m
            jalpha2 = falpha2.GetParameter(0) + falpha2.GetParameter(1)*m + falpha2.GetParameter(2)*m*m
            jslope2 = fslope2.GetParameter(0) + fslope2.GetParameter(1)*m + fslope2.GetParameter(2)*m*m

        inorm.SetPoint(inorm.GetN(), m, syield)
        signalNorm[m].setVal(max(0., syield))

        imean.SetPoint(imean.GetN(), m, jmean)
        if jmean > 0: vmean[m].setVal(jmean)

        isigma.SetPoint(isigma.GetN(), m, jsigma)
        if jsigma > 0: vsigma[m].setVal(jsigma)

        ialpha1.SetPoint(ialpha1.GetN(), m, jalpha1)
        if not jalpha1==0: valpha1[m].setVal(jalpha1)

        islope1.SetPoint(islope1.GetN(), m, jslope1)
        if jslope1 > 0: vslope1[m].setVal(jslope1)
       
        ialpha2.SetPoint(ialpha2.GetN(), m, jalpha2)
        if not jalpha2==0: valpha2[m].setVal(jalpha2)

        islope2.SetPoint(islope2.GetN(), m, jslope2)
        if jslope2 > 0: vslope2[m].setVal(jslope2)


        #### newly introduced, not yet sure if helpful: 
        vmean[m].removeError()
        vsigma[m].removeError()
        valpha1[m].removeError()
        valpha2[m].removeError()
        vslope1[m].removeError()
        vslope2[m].removeError()

        #signalNorm[m].setConstant(False)  ## newly put here to ensure it's freely floating in the combine fit
 
    #c1 = TCanvas("c1", "Crystal Ball", 1200, 1200) #if not isAH else 1200
    #c1.Divide(2, 3)
    c1 = TCanvas("c1", "Crystal Ball", 1800, 800)
    c1.Divide(3, 2)
    c1.cd(1)
    gmean.SetMinimum(0.)
    gmean.Draw("APL")
    imean.Draw("P, SAME")
    drawRegion(category)
    c1.cd(2)
    gsigma.SetMinimum(0.)
    gsigma.Draw("APL")
    isigma.Draw("P, SAME")
    drawRegion(category)
    c1.cd(3)
    galpha1.Draw("APL")
    ialpha1.Draw("P, SAME")
    drawRegion(category)
    galpha1.GetYaxis().SetRangeUser(0., 1.1) #adjusted upper limit from 5 to 2
    c1.cd(4)
    gslope1.Draw("APL")
    islope1.Draw("P, SAME")
    drawRegion(category)
    gslope1.GetYaxis().SetRangeUser(0., 150.) #adjusted upper limit from 125 to 60
    if True: #isAH:
        c1.cd(5)
        galpha2.Draw("APL")
        ialpha2.Draw("P, SAME")
        drawRegion(category)
        galpha2.GetYaxis().SetRangeUser(0., 2.)
        c1.cd(6)
        gslope2.Draw("APL")
        islope2.Draw("P, SAME")
        drawRegion(category)
        gslope2.GetYaxis().SetRangeUser(0., 20.)

    c1.Print(PLOTDIR+"MC_bstar_"+YEAR+"/"+stype+"_"+category+"_SignalShape.pdf")
    c1.Print(PLOTDIR+"MC_bstar_"+YEAR+"/"+stype+"_"+category+"_SignalShape.png")

    c2 = TCanvas("c2", "Signal Efficiency", 800, 600)
    c2.cd(1)
    gnorm.SetMarkerColor(cColor)
    gnorm.SetMarkerStyle(20)
    gnorm.SetLineColor(cColor)
    gnorm.SetLineWidth(2)
    gnorm.Draw("APL")
    inorm.Draw("P, SAME")
    gnorm.GetXaxis().SetRangeUser(genPoints[0]-100, genPoints[-1]+100)
    gnorm.GetYaxis().SetRangeUser(0., gnorm.GetMaximum()*1.25)
    #drawCMS(-1, "Simulation Preliminary", year=YEAR)
    #drawCMS(-1, "Work in Progress", year=YEAR, suppressCMS=True) 
    drawCMS(-1, "", year=YEAR, suppressCMS=True) 
    drawAnalysis(category)
    drawRegion(category)
    c2.Print(PLOTDIR+"MC_bstar_"+YEAR+"/"+stype+"_"+category+"_SignalNorm.pdf")
    c2.Print(PLOTDIR+"MC_bstar_"+YEAR+"/"+stype+"_"+category+"_SignalNorm.png")


    #*******************************************************#
    #                                                       #
    #                   Generate workspace                  #
    #                                                       #
    #*******************************************************#

    # create workspace
    w = RooWorkspace("bstar_"+YEAR, "workspace")
    for m in massPoints:
        getattr(w, "import")(signal[m], RooFit.Rename(signal[m].GetName()))
        getattr(w, "import")(signalNorm[m], RooFit.Rename(signalNorm[m].GetName()))
        getattr(w, "import")(signalXS[m], RooFit.Rename(signalXS[m].GetName()))
    w.writeToFile(WORKDIR+"MC_signal_%s_%s.root" % (YEAR, category), True)  
    print "Workspace", WORKDIR+"MC_signal_%s_%s.root" % (YEAR, category), "saved successfully"


def drawPlot(name, channel, variable, model, dataset, fitRes=[], norm=-1, reg=None, cat="", alt=None, anorm=-1, signal=None, snorm=-1):
    isData = norm>0
    isMass = "Mass" in name
    isSignal = '_M' in name
    mass = name[8:12]
    isCategory = reg is not None
    #isBottomPanel = not isSignal
    isBottomPanel = True
    postfix = "Mass" if isMass else ('SR' if 'SR' in name else ('SB' if 'SB' in name else ""))
    cut = "reg==reg::"+cat if reg is not None else ""
    normRange = "h_extended_reasonable_range" if isMass else "X_reasonable_range"
    dataRange = "LSBrange,HSBrange" if isMass and isData else normRange

    cmsLabel = "Preliminary" if isData else "Simulation Preliminary"
    #if not type(fitRes) is list: cmsLabel = "Preliminary"
    if 'paper' in name: cmsLabel = ""
    pullRange = 5

    dataMin, dataMax = array('d', [0.]), array('d', [0.])
    dataset.getRange(variable, dataMin, dataMax)
    xmin, xmax = dataMin[0], dataMax[0]

    lastBin = variable.getMax()
    if not isMass and not isSignal:
        if 'nn' in channel or 'll' in channel or 'ee' in channel or 'mm' in channel: lastBin = 3500.
        else: lastBin = 4500.

    # ====== CONTROL PLOT ======
    c = TCanvas("c_"+name, "Fitting "+name, 800, 800 if isBottomPanel else 600)
    if isBottomPanel:
        c.Divide(1, 2)
        setTopPad(c.GetPad(1), RATIO)
        setBotPad(c.GetPad(2), RATIO)
    else: setPad(c.GetPad(0))
    c.cd(1)
    frame = variable.frame()
    if isBottomPanel: setPadStyle(frame, 1.25, True)

    # Plot Data
    data, res = None, None
    if dataset is not None: data = dataset.plotOn(frame, RooFit.Cut(cut), RooFit.Binning(variable.getBinning("PLOT")), RooFit.DataError(RooAbsData.Poisson if isData else RooAbsData.SumW2), RooFit.Range(dataRange), RooFit.DrawOption("PE0"), RooFit.Name("data_obs"))
    if data is not None and isData: fixData(data.getHist(), True)

    # Simple fit
    if isCategory:
        if type(fitRes) is list:
            for f in fitRes:
                if f is not None:
                    model.plotOn(frame, RooFit.Slice(reg, cat), RooFit.ProjWData(RooArgSet(reg), dataset), RooFit.VisualizeError(f, 1, False), RooFit.SumW2Error(True), RooFit.FillColor(1), RooFit.FillStyle(3002))
                    if VERBOSE: model.plotOn(frame, RooFit.Slice(reg, cat), RooFit.ProjWData(RooArgSet(reg), dataset), RooFit.VisualizeError(f), RooFit.SumW2Error(True), RooFit.FillColor(2), RooFit.FillStyle(3004))
        elif fitRes is not None: frame.addObject(fitRes, "E3")
        model.plotOn(frame, RooFit.Slice(reg, cat), RooFit.ProjWData(RooArgSet(reg), dataset), RooFit.LineColor(getColor(name, channel)))
        res = frame.pullHist()
        if alt is not None: alt.plotOn(frame, RooFit.Normalization(anorm, RooAbsReal.NumEvent), RooFit.LineStyle(7), RooFit.LineColor(922), RooFit.Name("Alternate"))
    else:
        if type(fitRes) is list:
            for f in fitRes:
                if f is not None:
                    model.plotOn(frame, RooFit.VisualizeError(f, 1, False), RooFit.Normalization(norm if norm>0 or dataset is None else dataset.sumEntries(), RooAbsReal.NumEvent), RooFit.SumW2Error(True), RooFit.Range(normRange), RooFit.FillColor(1), RooFit.FillStyle(3002), RooFit.DrawOption("F"))
                    if VERBOSE: model.plotOn(frame, RooFit.VisualizeError(f), RooFit.Normalization(norm if norm>0 or dataset is None else dataset.sumEntries(), RooAbsReal.NumEvent), RooFit.SumW2Error(True), RooFit.Range(normRange), RooFit.FillColor(2), RooFit.FillStyle(3004), RooFit.DrawOption("F"))
                model.paramOn(frame, RooFit.Label(model.GetTitle()), RooFit.Layout(0.5, 0.95, 0.94), RooFit.Format("NEAU"))
        elif fitRes is not None: frame.addObject(fitRes, "E3")
        model.plotOn(frame, RooFit.LineColor(getColor(name, channel)), RooFit.Range(normRange), RooFit.Normalization(norm if norm>0 or dataset is None else dataset.sumEntries(), RooAbsReal.NumEvent)) #RooFit.Normalization(norm if norm>0 or dataset is None else dataset.sumEntries(), RooAbsReal.NumEvent)
        res = frame.pullHist() #if not isSignal else frame.residHist()
        # plot components
        for comp in ["baseTop", "gausW", "gausT", "baseVV", "gausVW", "gausVZ", "gausVH"]: model.plotOn(frame, RooFit.LineColor(getColor(name, channel)), RooFit.Range(normRange), RooFit.LineStyle(2), RooFit.Components(comp), RooFit.Normalization(norm if norm>0 or dataset is None else dataset.sumEntries(), RooAbsReal.NumEvent))
        if alt is not None: alt.plotOn(frame, RooFit.Range(normRange), RooFit.LineStyle(7), RooFit.LineColor(922), RooFit.Name("Alternate"))

    # Replot data
    if dataset is not None: data = dataset.plotOn(frame, RooFit.Cut(cut), RooFit.Binning(variable.getBinning("PLOT")), RooFit.DataError(RooAbsData.Poisson if isData else RooAbsData.SumW2), RooFit.Range(dataRange), RooFit.DrawOption("PE0"), RooFit.Name("data_obs"))

    if not isMass and not isSignal: # Log scale
        frame.SetMaximum(frame.GetMaximum()*10)
        frame.SetMinimum(max(frame.SetMinimum(), 8.e-2 if isData else 1.e-4))
        c.GetPad(1).SetLogy()
    else:
        frame.GetYaxis().SetRangeUser(0, frame.GetMaximum())
        frame.SetMaximum(frame.GetMaximum()*1.25)
        frame.SetMinimum(0)
    #frame.GetYaxis().SetTitleOffset(frame.GetYaxis().GetTitleOffset()*0.8)
    frame.GetYaxis().SetTitleOffset(1.4)
    frame.Draw()
    #drawCMS(LUMI, cmsLabel)
    #drawCMS(LUMI, "Work in Progress", suppressCMS=True)
    drawCMS(LUMI, "", suppressCMS=True)
    drawAnalysis(channel)
    drawRegion(channel + ("" if isData and not isCategory else ('SR' if 'SR' in name else ('SB' if 'SB' in name else ""))), True)
    if isSignal: drawMass("M_{Z'} = "+mass+" GeV")

    if isBottomPanel:
        c.cd(2)
        frame_res = variable.frame()
        setPadStyle(frame_res, 1.25)
        #res = frame.residHist()
        if res is not None and isData: fixData(res)
        if dataset is not None: frame_res.addPlotable(res, "P")
        setBotStyle(frame_res, RATIO, False)
        frame_res.GetYaxis().SetRangeUser(-pullRange, pullRange)
        #frame_res.GetYaxis().SetTitleOffset(frame_res.GetYaxis().GetTitleOffset()*0.4)
        frame_res.GetYaxis().SetTitle("pulls (#sigma)")
        frame_res.GetYaxis().SetTitleOffset(0.4)
        frame_res.Draw()
        chi2, nbins, npar = 0., 0, 0
        if not res==None:
            for i in range(0, res.GetN()):
                if data.getHist().GetY()[i] > 1.e-3:
                    nbins = nbins + 1
                    chi2 += res.GetY()[i]**2

        #if isData and not isMass:
        frame.GetXaxis().SetRangeUser(variable.getMin(), lastBin)
        frame_res.GetXaxis().SetRangeUser(variable.getMin(), lastBin)
        line_res = drawLine(frame_res.GetXaxis().GetXmin(), 0, lastBin, 0)

    c.SaveAs(PLOTDIR+"MC_signal_"+YEAR+"/"+name+".pdf")
    c.SaveAs(PLOTDIR+"MC_signal_"+YEAR+"/"+name+".png")
    #if VERBOSE: raw_input("Press Enter to continue...")
    # ======   END PLOT   ======


if __name__ == "__main__":
    if options.category!='':
        signal(options.category)
    else:
        for c in categories:
            p = multiprocessing.Process(target=signal, args=(c,)) 
            jobs.append(p)
            p.start()
