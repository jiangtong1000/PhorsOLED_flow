import os
import sys
import json

jobtype = sys.argv[1]
f = open(f'jobids_{a}.json', "r")
jobids = json.loads(f.read())
for ikey in jobids.keys():
    os.system(f"lbg job download -p {ikey}/{jobtype} {jobids[ikey]}")
