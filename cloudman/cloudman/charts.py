import os 
os.environ['HOME']='/var/www/tmp'

import random
import django
import datetime

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter

def HepSpecsAllocationPieChart(request):
    fig = Figure(figsize=(4,4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    #ax.plot([1,2,3])
    labels = 'Allocated', 'Free'
    fracs = [10,90]
    #ax.pie(fracs, labels=labels)
    ax.pie(fracs, explode=None, labels=labels, colors=('r', 'g', 'b', 'c', 'm', 'y', 'k', 'w'),
         autopct='%1.1f%%', pctdistance=0.6, labeldistance=1.1, shadow=False)
    ax.set_title('Top Level Allocation')
    ax.grid(True)
    #ax.set_xlabel('time')
    #ax.set_ylabel('volts')
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response)
    canvas.draw()
    return response

def MemoryAllocationPieChart(request):
    fig = Figure(figsize=(4,4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    #ax.plot([1,2,3])
    labels = 'Allocated', 'Free'
    fracs = [10,90]
    #ax.pie(fracs, labels=labels)
    ax.pie(fracs, explode=None, labels=labels, colors=('r', 'g', 'b', 'c', 'm', 'y', 'k', 'w'),
         autopct='%1.1f%%', pctdistance=0.6, labeldistance=1.1, shadow=False)
    ax.set_title('Top Level Allocation')
    ax.grid(True)
    #ax.set_xlabel('time')
    #ax.set_ylabel('volts')
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response)
    canvas.draw()
    return response

def StorageAllocationPieChart(request):
    fig = Figure(figsize=(4,4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    #ax.plot([1,2,3])
    labels = 'Allocated', 'Free'
    fracs = [10,90]
    #ax.pie(fracs, labels=labels)
    ax.pie(fracs, explode=None, labels=labels, colors=('r', 'g', 'b', 'c', 'm', 'y', 'k', 'w'),
         autopct='%1.1f%%', pctdistance=0.6, labeldistance=1.1, shadow=False)
    ax.set_title('Top Level Allocation')
    ax.grid(True)
    #ax.set_xlabel('time')
    #ax.set_ylabel('volts')
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response)
    canvas.draw()
    return response

def BandwidthAllocationPieChart(request):
    fig = Figure(figsize=(4,4)) 
    canvas = FigureCanvas(fig) 
    ax = fig.add_subplot(111) 
    #ax.plot([1,2,3]) 
    labels = 'Allocated', 'Free' 
    fracs = [10,90] 
    #ax.pie(fracs, labels=labels)
    ax.pie(fracs, explode=None, labels=labels, colors=('r', 'g', 'b', 'c', 'm', 'y', 'k', 'w'),
   	 autopct='%1.1f%%', pctdistance=0.6, labeldistance=1.1, shadow=False)
    ax.set_title('Top Level Allocation') 
    ax.grid(True) 
    #ax.set_xlabel('time') 
    #ax.set_ylabel('volts') 
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response)
    canvas.draw() 
    return response 

def example(request):
    fig=Figure()
    ax=fig.add_subplot(111)
    x=[]
    y=[]
    now=datetime.datetime.now()
    delta=datetime.timedelta(days=1)
    for i in range(10):
        x.append(now)
        now+=delta
        y.append(random.randint(0, 1000))
    ax.plot_date(x, y, '-')
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
