{
  TChain* ntu = new TChain("tree");
  ntu->Add("/eos/cms/store/group/phys_exotica/dijet/Dijet13TeV/magda/reduced_trees_2016_07Aug2017_JEC_07Aug2017_V11/*reduced_skim.root");


  std::cout << ntu->GetEntries() << std::endl;
  ntu->Scan("run:lumi:event:etaAK4_j1:phiAK4_j1:pTAK4_j1:chargedHadEnFrac_j1:neutrHadEnFrac_j1:chargedElectromFrac_j1:neutrElectromFrac_j1:muEnFract_j1:etaAK4_j2:phiAK4_j2:pTAK4_j2:chargedHadEnFrac_j2:neutrHadEnFrac_j2:chargedElectromFrac_j2:neutrElectromFrac_j2:muEnFract_j2:mjj","mjj>6500 && abs(deltaETAjj)<1.1")

}
