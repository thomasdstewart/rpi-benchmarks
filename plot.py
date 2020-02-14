#!/usr/bin/env python3
import sys
import matplotlib.pyplot
from pprint import pprint as pp

data = {}
for line in open("README.md", "r"):
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
            
## All data
fig, ax = matplotlib.pyplot.subplots(figsize=(10, 10))
fig.canvas.set_window_title('Raspberry Pi armhf vs arm64')
fig.subplots_adjust(left=0.07, right=0.98, bottom=0.35, top=0.97, wspace=0.2, hspace=0.2)
ax.set_title('Raspberry Pi armhf vs arm64')
ax.set_ylabel('Time (minutes)')
ax.set_xticklabels(data.keys(), rotation=90)

d = []
for k in data.keys():
    print("%s: %s" % (k, round(sum(data[k]) / len(data[k]),2)))
    d.append(data[k])
ax.boxplot(d)

#matplotlib.pyplot.show()
matplotlib.pyplot.savefig('plot.png')

## armhf
fig, ax = matplotlib.pyplot.subplots(figsize=(10, 10))
fig.canvas.set_window_title('Raspberry Pi armhf')
fig.subplots_adjust(left=0.07, right=0.98, bottom=0.35, top=0.97, wspace=0.2, hspace=0.2)
ax.set_title('Raspberry Pi armhf')
ax.set_ylabel('Time (minutes)')

d = []
y = []
for k in data.keys():
    if(k.find("32bit") > 0):
        d.append(data[k])
        y.append(k)
ax.set_xticklabels(y, rotation=90)
ax.boxplot(d)

#matplotlib.pyplot.show()
matplotlib.pyplot.savefig('plot32.png')

## armh64
fig, ax = matplotlib.pyplot.subplots(figsize=(10, 10))
fig.canvas.set_window_title('Raspberry Pi arm64')
fig.subplots_adjust(left=0.07, right=0.98, bottom=0.35, top=0.97, wspace=0.2, hspace=0.2)
ax.set_title('Raspberry Pi arm64')
ax.set_ylabel('Time (minutes)')

d = []
y = []
for k in data.keys():
    if(k.find("64bit") > 0):
        d.append(data[k])
        y.append(k)
ax.set_xticklabels(y, rotation=90)
ax.boxplot(d)

#matplotlib.pyplot.show()
matplotlib.pyplot.savefig('plot64.png')
