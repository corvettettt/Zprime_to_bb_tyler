#! /usr/bin/env python

###
### contains the selections for each b-tagging category, as well as the pre-selection
###

dijet_bins = [1, 3, 6, 10, 16, 23, 31, 40, 50, 61, 74, 88, 103, 119, 137, 156, 176, 197, 220, 244, 270, 296, 325, 354, 386, 419, 453, 489, 526, 565, 606, 649, 693, 740, 788, 838, 890, 944, 1000, 1058, 1118, 1181, 1246, 1313, 1383, 1455, 1530, 1607, 1687, 1770, 1856, 1945, 2037, 2132, 2231, 2332, 2438, 2546, 2659, 2775, 2895, 3019, 3147, 3279, 3416, 3558, 3704, 3854, 4010, 4171, 4337, 4509, 4686, 4869, 5058, 5253, 5455, 5663, 5877, 6099, 6328, 6564, 6808, 7060, 7320, 7589, 7866, 8152, 8447, 8752, 9067, 9391, 9726, 10072, 10430, 10798, 11179, 11571, 11977, 12395, 12827, 13272, 13732, 14000]

working_points = {'loose': 1, 'medium': 2, 'tight': 3}

reduced_triggers = "(HLT_PFHT1050==1 || HLT_PFHT900==1 || HLT_PFJet500==1 || HLT_PFJet550==1 || HLT_CaloJet500_NoJetID==1 || HLT_CaloJet550_NoJetID==1 || HLT_AK8PFJet500==1 || HLT_AK8PFJet550==1)"

triggers = "(HLT_PFHT1050==1 || HLT_PFHT900==1 || HLT_PFJet500==1 || HLT_PFJet550==1 || HLT_CaloJet500_NoJetID==1 || HLT_CaloJet550_NoJetID==1 || HLT_AK8PFJet500==1 || HLT_AK8PFJet550==1 || HLT_DoublePFJets100_CaloBTagDeepCSV_p71==1 || HLT_DoublePFJets116MaxDeta1p6_DoubleCaloBTagDeepCSV_p71==1 || HLT_DoublePFJets128MaxDeta1p6_DoubleCaloBTagDeepCSV_p71==1 || HLT_DoublePFJets200_CaloBTagDeepCSV_p71==1 || HLT_DoublePFJets350_CaloBTagDeepCSV_p71==1 || HLT_DoublePFJets40_CaloBTagDeepCSV_p71==1)"

triggers_PFHT   = "(HLT_PFHT1050==1 || HLT_PFHT900==1)"
triggers_Jet    = "(HLT_PFJet500==1 || HLT_PFJet550==1 || HLT_CaloJet500_NoJetID==1 || HLT_CaloJet550_NoJetID==1 || HLT_AK8PFJet500==1 || HLT_AK8PFJet550==1)"
triggers_BTag   = "(HLT_DoublePFJets100_CaloBTagDeepCSV_p71==1 || HLT_DoublePFJets116MaxDeta1p6_DoubleCaloBTagDeepCSV_p71==1 || HLT_DoublePFJets128MaxDeta1p6_DoubleCaloBTagDeepCSV_p71==1 || HLT_DoublePFJets200_CaloBTagDeepCSV_p71==1 || HLT_DoublePFJets350_CaloBTagDeepCSV_p71==1 || HLT_DoublePFJets40_CaloBTagDeepCSV_p71==1)"

AK8veto = " && !(fatjetmass_1>65 && fatjetmass_2>65)"
electronVeto = " && nelectrons<1"
muonVeto = " && nmuons<1"

tight_jetID = " && jid_1>5 && jid_2>5"

preselection = "jj_mass_widejet>1530 && jj_deltaEta_widejet<1.1 && "

alias = { ## the same as above with the new btag_WP variable
    "preselection_noveto" : "jj_mass_widejet>1530 && jj_deltaEta_widejet<1.1"+tight_jetID+" && "+reduced_triggers,
    "preselection" : preselection+triggers+tight_jetID+AK8veto+electronVeto+muonVeto,
    "2b" : preselection+triggers+tight_jetID+AK8veto+electronVeto+muonVeto+" && jbtag_WP_1>={WP} && jbtag_WP_2>={WP}",
    "1b" : preselection+triggers+tight_jetID+AK8veto+electronVeto+muonVeto+" && ((jbtag_WP_1>={WP} && jbtag_WP_2<{WP}) || (jbtag_WP_1<{WP} && jbtag_WP_2>={WP}))",
    "2mu": preselection+triggers+tight_jetID+AK8veto+electronVeto+muonVeto+" && jbtag_WP_1<{WP} && jbtag_WP_2<{WP} && jnmuons_1>0 && jnmuons_2>0"
}

aliasSM = { ## a new btagging category that is semi medium, semi loose.
    "preselection_noveto" : "jj_mass_widejet>1530 && jj_deltaEta_widejet<1.1"+tight_jetID,
    "preselection" : preselection+triggers+tight_jetID+AK8veto+electronVeto+muonVeto,
    "2b" : preselection+triggers+tight_jetID+AK8veto+electronVeto+muonVeto+" && ((jbtag_WP_1>=2 && jbtag_WP_2>=1) || (jbtag_WP_1>=1 && jbtag_WP_2>=2))",
    "1b" : preselection+triggers+tight_jetID+AK8veto+electronVeto+muonVeto+" && ((jbtag_WP_1>=2 && jbtag_WP_2<1) || (jbtag_WP_1<1 && jbtag_WP_2>=2))",
    "2mu": preselection+triggers+tight_jetID+AK8veto+electronVeto+muonVeto+" && jbtag_WP_1<2 && jbtag_WP_2<2 && jnmuons_1>0 && jnmuons_2>0"
}

alias["bb"] = alias["2b"]
alias["bq"] = alias["1b"]
alias["mumu"] = alias["2mu"]
alias["qq"] = alias["preselection"]
alias['none'] = 'jj_deltaEta<1.1'

aliasSM["bb"] = aliasSM["2b"]
aliasSM["bq"] = aliasSM["1b"]
aliasSM["mumu"] = aliasSM["2mu"]
aliasSM["qq"] = aliasSM["preselection"]
aliasSM['none'] = 'jj_deltaEta<1.1'

additional_selections = {"": "", "AK8veto": " && !(fatjetmass_1>65 && fatjetmass_2>65)", "electronVeto": " && nelectrons<1", "muonVeto": " && nmuons<1"}

additional_selections['leptonVeto'] = additional_selections['electronVeto']+additional_selections['muonVeto']
additional_selections['fullVeto'] = additional_selections['AK8veto']+additional_selections['leptonVeto']


