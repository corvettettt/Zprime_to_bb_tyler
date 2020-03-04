{
  TChain* ntu = new TChain("tree");
  ntu->Add("/afs/cern.ch/work/m/msommerh/public/Zprime_to_bb_Analysis/Skim/data_2016_*.root");


  std::cout << ntu->GetEntries() << std::endl;
  ntu->Scan("jeta_1:jphi_1:jpt_1:jnconst_1:jchf_1:jnhf_1:jcef_1:jnef_1:jmuf_1:jeta_2:jphi_2:jpt_2:jnconst_2:jchf_2:jnhf_2:jcef_2:jnef_2:jmuf_2:jj_mass:jj_mass_widejet","jj_mass_widejet>6500 && abs(jj_deltaEta_widejet)<1.1")

}
