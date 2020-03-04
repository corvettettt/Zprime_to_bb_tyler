#! /usr/bin/env python

import os, sys, getopt
import copy
import time
import math
import ROOT
from array import array
from ROOT import gROOT, gRandom, gStyle
from ROOT import TFile, TTree, TCut, TH1F, TH2F, TGraph, TGraph2D, TGraphAsymmErrors, TMultiGraph, TObjArray, TGraphSmooth
from ROOT import TStyle, TCanvas, TPad
from ROOT import TLegend, TLatex, TText, TColor

from utils import drawCMS, drawAnalysis
#from theory import THEORY

import optparse
usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage)
parser.add_option("-b", "--bash", action="store_true", default=False, dest="bash")
parser.add_option("-B", "--blind", action="store_true", default=False, dest="blind")
parser.add_option("-c", "--category", action="store", type="string", dest="category", default="sl")
parser.add_option("-r", "--root", action="store_true", default=False, dest="root")
(options, args) = parser.parse_args()
category = options.category
if options.bash: gROOT.SetBatch(True)
#gStyle.SetOptStat(0)
gStyle.SetHatchesSpacing(1)
gStyle.SetHatchesLineWidth(2) # default is 1

LUMI = 137200
ZpToBB = 0.1293

# model B: g = 0.646879, cH = 0.976246, cF = 1.02433 
# model A: g = 0.648943, cH = -0.555969, cF = -1.3159

massPoints = [2000, 2500, 3000]
massColors = {2000 : 798, 2500 : 625, 3000: 856, 4000: 856 }
massFill = {2000 : 3013, 2500 : 3005, 3000: 3004, 4000: 3004 }
massLabels = {2000 : [1.1, 0.04], 2500 : [1.1, 0.04], 3000 : [1.3, 0.25], 4000 : [2, 0.45]}
models_point = {'A1' : [-0.555969, -0.554161], 'A3' : [-0.1447,-0.1447], 'B3' : [-2.928738, 0.142877796174]} #'A1' : [-0.4225,-0.43278]
models_color = {'A1' : 616-3, 'B3' : 629}
models_style = {'A1' : 34, 'B3' : 20}
models_name = {'A1' : "HVT model A", 'A3' : "model A (g_{V} = 3) ", 'B3' : "HVT model B"}
# This is sigma x Br(X->bb) [pb]
observed = {2000 : 19., 2500 : 19., 3000 : 13., 4000 : 6.}
width = 0.05


def hvt(benchmark = ['B3', 'A1']):
    
    hxs = {}
    hw = {}
    gxs = {}
    gw = {}
    mg = TMultiGraph()
    
    for m in massPoints:
        
        hxs[m] = TH2F("hxs_M%d" % m, ";;", 50, -0.04, 3.96, 100,  0., 2.)
        hw[m] = TH2F("hw_M%d" % m, ";;", 50, -0.04, 3.96, 50,  0., 2.)

    for m in massPoints:
        file = TFile.Open("HVT/scanHVT_M%s.root" % m, "READ")
        tree = file.Get("tree")
        for entry in range(tree.GetEntries()): # Fill mass points only if NOT excluded
            tree.GetEntry(entry)
            gH, gF = tree.gv*tree.ch, tree.g*tree.g*tree.cq/tree.gv
            XsBr = tree.CX0 * tree.BRbb * 1000. # in fb
            if XsBr < observed[m]: hxs[m].Fill(gH, gF)
            if tree.total_widthV0/float(m) < width: hw[m].Fill(gH, gF)

        
        for b in range(hxs[m].GetNbinsX()*hxs[m].GetNbinsY()):
            hxs[m].SetBinContent(b, 1. if hxs[m].GetBinContent(b)>0. else 0.)
            hw[m].SetBinContent(b, 1. if hw[m].GetBinContent(b)>0. else 0.)
        
        #hxs[m].Smooth(20)
        #hw[m].Smooth(20)
        
        gxs[m] = getCurve(hxs[m])
        for i, g in enumerate(gxs[m]):
            g.SetLineColor(massColors[m])
            g.SetFillColor(massColors[m])
            g.SetFillStyle(massFill[m]) #(3345 if i>1 else 3354)
            g.SetLineWidth(503*(1 if i<2 else -1))
            mg.Add(g)
        
        if m==3000:
            gw[m] = getCurve(hw[m])
            for i, g in enumerate(gw[m]):
                g.SetPoint(0, 0., g.GetY()[0])
                g.SetLineWidth(501*(1 if i<2 else -1))
                g.SetLineColor(920+2)
                g.SetFillColor(920+1)
                g.SetFillStyle(3003)
                mg.Add(g)
    
    if options.root:
        outFile = TFile("plotsLimit/Model.root", "RECREATE")
        outFile.cd()
        for m in massPoints:
            mg[m].Write("X_M%d" % m)
        mgW.Write("width")
        outFile.Close()
        print "Saved histogram in file plotsLimit/Model.root, exiting..."
        exit()
    
    
    ### plot ###
    
    c1 = TCanvas("c1", "HVT Exclusion Limits", 800, 600)
    c1.cd()
    c1.GetPad(0).SetTopMargin(0.06)
    c1.GetPad(0).SetRightMargin(0.05)
    c1.GetPad(0).SetTicks(1, 1)
    mg.Draw("AC")
    #mg.GetXaxis().SetTitle("g_{V} c_{H}")
    mg.GetXaxis().SetTitle("Higgs and vector boson coupling g_{H}")
    mg.GetXaxis().SetRangeUser(-3.,3.)
    mg.GetXaxis().SetLabelSize(0.045)
    mg.GetXaxis().SetTitleSize(0.045)
    mg.GetXaxis().SetTitleOffset(1.)
    #mg.GetYaxis().SetTitle("g^{2} c_{F} / g_{V}")
    mg.GetYaxis().SetTitle("Fermion coupling g_{F}")
    mg.GetYaxis().SetLabelSize(0.045)
    mg.GetYaxis().SetTitleSize(0.045)
    mg.GetYaxis().SetTitleOffset(1.)
    mg.GetYaxis().SetRangeUser(-1., 1.)
    mg.GetYaxis().SetNdivisions(505)
#    hxs[3500].Draw("CONTZ")
    
    drawCMS(LUMI, "", False) #Preliminary
#    drawAnalysis("XVH"+category, False)
#    latex = TLatex()
#    latex.SetNDC()
#    latex.SetTextFont(62)
#    latex.SetTextSize(0.06)
#    latex.DrawLatex(0.10, 0.925, "CMS")

    # model B
    g_model = {}
    for i, b in enumerate(benchmark):
        g_model[i] = TGraph(1)
        g_model[i].SetTitle(models_name[b])
        g_model[i].SetPoint(0, models_point[b][0], models_point[b][1])
        g_model[i].SetMarkerStyle(models_style[b])
        g_model[i].SetMarkerColor(models_color[b])
        g_model[i].SetMarkerSize(1.5)
        g_model[i].Draw("PSAME")
    
    # text
    latex = TLatex()
    latex.SetTextSize(0.045)
    latex.SetTextFont(42)
    latex.SetTextColor(630)
#    for b in benchmark: latex.DrawLatex(models_point[b][0]+0.02, models_point[b][1]+0.02, models_name[b])
    latex.SetTextColor(920+2)
    latex.DrawLatex(-2.8, -0.875, "#frac{#Gamma_{Z'}}{m_{Z'}} > %.0f%%" % (width*100, ))
    
    leg = TLegend(0.68, 0.60, 0.95, 0.94)
    leg.SetBorderSize(1)
    leg.SetFillStyle(1001)
    leg.SetFillColor(0)
    for m in massPoints:
        leg.AddEntry(gxs[m][0], "m_{Z'} = %.1f TeV" % (m/1000.), "fl")
    for i, b in enumerate(benchmark):
        leg.AddEntry(g_model[i], g_model[i].GetTitle(), "P")
    leg.SetY1(leg.GetY2()-leg.GetNRows()*0.050)
    leg.SetMargin(0.35)
    leg.Draw()
    
    gxs_ = gxs[massPoints[0]][0].Clone("gxs_")
    gxs_.SetLineColor(1)
#    gxs_.SetFillColor(1)
    
    latex.SetNDC()
    latex.SetTextColor(1)
    latex.SetTextSize(0.04)
    latex.SetTextFont(52)
    latex.DrawLatex(0.15, 0.95, "q#bar{q} #rightarrow Z' #rightarrow b#bar{b}")
    
    c1.Print("plots/model/HVT.png")
    c1.Print("plots/model/HVT.pdf")
    c1.Print("plots/model/HVT.root")
    c1.Print("plots/model/HVT.C")
    
    #g = 0.646879, cH = 0.976246, cF = 1.02433
    print "model B = [", 3*0.976246, ",", 0.646879*0.646879*1.02433/3, "]"
    
    if not gROOT.IsBatch(): raw_input("Press Enter to continue...")
    
    


def getCurve(h):

    # Temporary draw
    c = TCanvas()
    c.cd()
    h.Smooth()
    h.SetContour(2)
    #h.Draw("COLZ")
    h.Draw("CONT Z LIST")
    c.Update()

    # Get contours
    curves = []
    conts = TObjArray(gROOT.GetListOfSpecials().FindObject("contours"))
    gs = TGraphSmooth("normal")
    gin = TGraph(conts.At(0).At(0))
    gout = gs.SmoothSuper(gin, "", 3)

    x_m = array('d', [])
    x_p = array('d', [])
    y_m = array('d', [])
    y_p = array('d', [])

    for p in xrange(0, gout.GetN()):
        gr_x = ROOT.Double(0.)
        gr_y = ROOT.Double(0.)
        gout.GetPoint(p, gr_x, gr_y)
        x_m.append(-gr_x)
        y_m.append(-gr_y)
        x_p.append(gr_x)
        y_p.append(gr_y)

#        if opt == 'w':
#            x_p[0] = 0.
#            x_m[0] = 0.

    curves.append(TGraph(len(x_p), x_p, y_p))
    curves.append(TGraph(len(x_m), x_m, y_m))
    curves.append(TGraph(len(x_p), x_p, y_m))
    curves.append(TGraph(len(x_m), x_m, y_p))

    c.Close()  

    return curves


if __name__ == "__main__":
    hvt()
