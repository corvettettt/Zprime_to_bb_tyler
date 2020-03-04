import glob,os

for i in glob.glob('*0.txt'):
  readable = False
  with open(i) as fin:
    content = ''' <<< Combine >>>
>>> method used is AsymptoticLimits
>>> random number generator seed is 123456
/afs/cern.ch/work/z/zhixing/private/CMSSW_10_3_3/src/Zprime_to_bb/2017/../datacards/medium/bstar/combined/combined_2017_M4300_MC.txt

'''
    for line in fin.readlines():
      if 'AsymptoticLimits' in line:
        readable = True
      if readable:
	content+=line
  with open(i.replace('.txt','2.txt'),'w+') as fout:
    fout.write(content)

