import os

add = '/eos/cms/store/group/phys_exotica/dijet/Dijet13TeV/TylerW/NANOAOD/'

for i in ['2017']:
  for mass in [500] + range(1000,10000,1000):
    os.system('ls /eos/cms/store/group/phys_exotica/dijet/Dijet13TeV/TylerW/NANOAOD/bstar2jj/' +i +'/2017%dGeV.root > MC_bstar_%s_M%d.txt'%(mass,i,mass))
