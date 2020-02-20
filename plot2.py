#!/usr/bin/env python3
import sys
from pprint import pprint as pp

data = {}
for line in open("Raspbian.md", "r"):
    # find lines what have data in
    if(line.find("data:") != -1):
        # remove prefix to data, data tag and new lines
        line = line.replace(' 1. ','')
        line = line.replace(' data','')
        line = line.replace('\n','')

        # before colon is data label
        data[line.split(':')[0]] = []

        # after colon is data
        readings = line.split(':')[1]
        # data is space seperated
        for reading in readings.split(' '):
            #ignore empty fields
            if(reading == ''):
                continue
            #data looks like: 55m7.511s
            #remove final 's' seconds unit
            reading = reading.replace('s','')
            #split on m, left is minutes right is seconds
            m = float(reading.split('m')[0])
            s = float(reading.split('m')[1])
            #calculate total minutes
            t = ((m * 60) + s) / 60
            #truncate
            t = round(t, 2)

            data[line.split(':')[0]].append(t)
            
d = []
for k in data.keys():
    print("%s: %s" % (k, round(sum(data[k]) / len(data[k]),2)))

