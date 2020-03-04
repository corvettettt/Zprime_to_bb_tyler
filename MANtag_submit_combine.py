#! /usr/bin/env python

###
### Macro for submitting the combine jobs for each mass point to HTCondor.
###

import global_paths
import sys
import os, re, glob
from commands import getoutput
from fnmatch import fnmatch
import itertools
from argparse import ArgumentParser
import json

if __name__ == "__main__":
  parser = ArgumentParser()
  parser.add_argument('-q', '--queue',   dest='queue', choices=['espresso', 'microcentury', 'longlunch', 'workday', 'tomorrow', 'testmatch', 'nextweek'], type=str, default='tomorrow', action='store',
                                         help="select queue for submission" )
  parser.add_argument('-y', '--year',    dest='year', type=str, default='2016', action='store', choices=['2016','2017','2018','run2', 'run2c'],
                                         help="set year, type run2 for combined submission." )
  parser.add_argument('-MC', '--isMC',   dest='isMC',  action='store_true', default=True,
                                         help="Select this if the sample is MC, otherwise it is flagged as data.")
  parser.add_argument("-b", "--btagging", action="store", type=str, dest="btagging", default="medium", choices=['tight', 'medium', 'loose', 'semimedium'])
  parser.add_argument("-c", "--category", action="store", type=str, dest="category", default="", choices=['', 'bb', 'bq', 'mumu'],
                                         help="Choose b-tagging category (bb, bq or mumu) if combine should run merely on a single category.")

  args = parser.parse_args()

#jobflavour = 'espresso' #max 30min
#jobflavour = 'microcentury' #max 1h
#jobflavour = 'longlunch' #max 2h
#jobflavour = 'workday' #max 8h
#jobflavour = 'tomorrow' #max 1d
#jobflavour = 'testmatch' #max 3d

else:
  args = None

YEAR=args.year
if YEAR=='run2c':
    print "running combine on separate fits for each year of run2..."
    YEAR='run2'
    separate_years=True
else:
    separate_years=False

mass_points = range(1600,8001,100)
nJobs = len(mass_points)

if separate_years and not YEAR=='run2':
    print "Separate year fit can only be selected if year is run2."
    sys.exit()

def submitJobs():
    path = global_paths.MAINDIR[:-1]
    workdir = global_paths.SUBMISSIONLOGS+"tmp_MANtag_combine{category}_{year}_{btagging}{suffix}".format(category="_"+args.category if args.category!="" else "", year=YEAR+'c' if separate_years else YEAR, btagging=args.btagging, suffix="_MC" if args.isMC else "")
    if not os.path.exists(workdir):
        os.makedirs(workdir)
        print "Directory "+workdir+" created."
    else:
        print "Directory "+workdir+" already exists."
    os.chdir(workdir)

    #submit job

    exefile = open(global_paths.MAINDIR+"MANtag_combine{}.sh".format("_single" if args.category!="" else ""), "r")
    execontents = exefile.readlines()
    exefile.close()
    execontents[7] = "main_dir='"+global_paths.MAINDIR+"'\n"
    exefile = open("./combine_{}_{}{}.sh".format(YEAR, args.btagging, "_"+args.category if args.category != "" else ""), 'w')
    exefile.writelines(execontents)
    exefile.close()

    os.system("chmod 755 combine_{}_{}{}.sh".format(YEAR, args.btagging, "_"+args.category if args.category != "" else ""))
    makeSubmitFileCondor(args.queue, nJobs)
    os.system("condor_submit submit.sub")
    print "jobs submitted"
    os.chdir("../..")

def makeSubmitFileCondor(jobflavour, nJobs):
    print "make options file for condor job submission"
    suffix=""
    input_year=str(YEAR)
    if separate_years: input_year+='c'
    if args.category!="": suffix+=" "+args.category
    submitfile = open("submit.sub", "w")
    submitfile.write("executable            = combine_{}_{}{}.sh\n".format(YEAR, args.btagging, "_"+args.category if args.category != "" else ""))
    submitfile.write("arguments             = "+str(int(args.isMC))+" "+input_year+" "+args.btagging+" $(ProcId)"+suffix+"\n")
    submitfile.write("output                = "+str(YEAR)+"_"+args.btagging+".$(ClusterId).$(ProcId).out\n")
    submitfile.write("error                 = "+str(YEAR)+"_"+args.btagging+".$(ClusterId).$(ProcId).err\n")
    submitfile.write("log                   = "+str(YEAR)+"_"+args.btagging+".$(ClusterId).log\n")
    submitfile.write('+JobFlavour           = "'+jobflavour+'"\n')
    submitfile.write('transfer_output_files = ""\n')
    submitfile.write("queue {}".format(nJobs))
    submitfile.close()

def main():

        submitJobs()

        print
        print "your jobs:"
        os.system("condor_q")
        userName=os.environ['USER']
        print
        print 'Done submitting jobs!'
        print

if __name__ == "__main__":
    print
    main()
    print "done"
