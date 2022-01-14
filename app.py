# app.py
# FLASK_APP=app.py FLASK_ENV=development flask run
from flask import Flask, render_template, request  # importing the render_template function
import os
import re
import readability
import difflib
from difflib import Differ
from difflib import SequenceMatcher

app = Flask(__name__,static_folder='static')
app.run(debug = True) 

datadir = "./data/"
defaultset = "YT - apac"

# home route
@app.route("/")
def hello():
    
    if request.args.get('dataset') == None:
        currentset = defaultset
    else:
        currentset = request.args.get('dataset')
    
    if request.args.get('search') == None:
        search = []
    else:
        search = request.args.get('search')
        search = search.split(',')
        search = [s.strip() for s in search]
        #print(search)
        
    datasets = loaddatasets()
    files = loadstream(currentset,search)
    diffs = loaddiffs(files,currentset)
    
    plot_png_main(files,diffs,search)
    #plot_png_search(files)
    
    #print(files)
    #print(diffs)
    
    return render_template('main.html', currentset = currentset, datasets = datasets, files = files, diffs = diffs, search = search)


def loaddatasets():
    
    datasets = []
    
    for file in os.listdir(datadir):
        datasets.append(file)
    
    datasets.sort()
    
    return datasets


def loadstream(dataset,search):
    
    files = []
    
    for file in os.listdir(datadir + dataset):
        if file.endswith(".txt"):
            
            tmpfile = {}
            
            tmpfile["filename"] = file
            p = re.compile(r'\d+')
            date = p.findall(file)[0][0:8]
            tmpfile["date"] = date[0:4] + "-" + date[4:6] + "-" + date[6:9]

            f = open(datadir + dataset + "/" + file,'r')
            tmpfile["text"] = f.read()
            
            tmpfile["readability"] = readability.getmeasures(tmpfile["text"], lang='en')
            tmpfile["readability"]["readability grades"]["GunningFogIndex"] = round(tmpfile["readability"]["readability grades"]["GunningFogIndex"],1)
            tmpfile["wordcount"] = tmpfile["readability"]["sentence info"]["words"]
    
            searches = []
            for query in search:
                searches.append((query,len(re.findall(query, tmpfile["text"], flags=re.IGNORECASE))))
            
            #print(searches)
            tmpfile["search"] = searches
    
            files.append(tmpfile)
    
    files = sorted(files, key=lambda x: x["filename"], reverse=False)
    #print(files)
    
    return files


def loaddiffs(files,dataset):
    
    diffs = []
    
    #print(files)
    
    for x in range(1,len(files)):
        
        tmpdiff = {}
        
        f1 = open(datadir + dataset + "/" + files[x-1]["filename"],'r')
        f2 = open(datadir + dataset + "/" + files[x]["filename"],'r')
        str1 = files[x-1]["text"]
        str2 = files[x]["text"]
        str1_lines = str1.splitlines()
        str2_lines = str2.splitlines()
        
        s = SequenceMatcher(a=str1, b=str2)
        tmpdiff["ratio"] = round(s.ratio(),4)
        
        d = difflib.Differ()
        tmpdiff["passages"] = list(d.compare(str1_lines, str2_lines))
        
        '''
        print(diff)
        #print('\n'.join(diff))
        for dif in diff:
            #print("!"+dif[0:2]+"!")
            if dif[0:2] != "  ":
                print(dif)
        '''
        
        diffs.append(tmpdiff)
    
    return diffs

import datetime
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
matplotlib.use('Agg')


def plot_png_main(files,diffs,search):
    
    plt.rcParams['font.size'] = 8
    plt.rcParams['axes.linewidth'] = 1
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.bottom'] = True
    plt.rcParams['axes.spines.left'] = True
    plt.rcParams['figure.dpi'] = 72
    plt.rcParams['lines.linewidth'] = 1
    plt.rcParams['lines.markersize'] = 5
    
    if len(search) == 0:
        plt.figure(figsize=(12, 2))
    else:
        plt.figure(figsize=(12, 2+len(search)))
    
    plt.axis('off')
    
    cmap = cm.YlOrRd
    norm = Normalize(vmin=10, vmax=50)
    
    dates = []
    wordcounts = []
    readabilities = []
    wordmax = 0
    for file in files:
        dates.append(datetime.datetime(int(file["date"][0:4]),int(file["date"][5:7]), int(file["date"][8:11]), 0, 0))
        wordcounts.append(file["wordcount"])
        readabilities.append(cmap(norm(file["readability"]["readability grades"]["GunningFogIndex"])))
        if wordmax < file["wordcount"]:
            wordmax = file["wordcount"]

    ratios = [1]
    for diff in diffs:
        ratios.append((1-diff["ratio"]) * wordmax)    
    
    if len(search) > 0:
        plotmain = plt.subplot2grid((2+len(search), 1), (0, 0), rowspan=2)
    else:
        plotmain = plt.subplot2grid((3, 1), (0, 0), rowspan=3)
    
    plotmain.margins(0.1, 0.1)
    plotmain.plot(dates,ratios,linestyle='', marker='o', color='r')
    plotmain.bar(dates,wordcounts,10,color=readabilities)
    
    if len(search) > 0:
        plots = []
        for i in range(0,len(search)):
            
            searchcounts = []
            for file in files:
                searchcounts.append(file["search"][i][1])
        
            plots.append(plt.subplot2grid((2+len(search), 1), (2+i, 0)))
            plots[i].margins(0.1, 0.1)
            plots[i].plot(dates,searchcounts,linestyle='--', marker='o', color='b')

    plt.tight_layout(pad=1)

    plt.savefig("static/plot_main.svg",format='svg')

'''
def plot_png_search(files):
    
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.linewidth'] = 1
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.bottom'] = True
    plt.rcParams['axes.spines.left'] = True
    plt.axis('off')
    cmap = cm.YlOrRd
    norm = Normalize(vmin=10, vmax=50)
    
    dates = []
    searchcounts = []
    for file in files:
        dates.append(datetime.datetime(int(file["date"][0:4]),int(file["date"][5:7]), int(file["date"][8:11]), 0, 0))
        searchcounts.append(file["searchcount"])
    
    
    plt.figure(figsize=(12,2),dpi=72)
    plt.plot(dates,searchcounts,linestyle='--', marker='o', color='b')
    plt.tight_layout()
    
    # saving the file.Make sure you 
    # use savefig() before show().
    plt.savefig("static/plot_search.svg",format='svg')
'''