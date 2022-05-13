#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from https://github.com/Shreeshrii/tesstrain-sanPlusMinus

import re
import os
import argparse
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
## from scipy.interpolate import UnivariateSpline

def parse_tesseract_log5(logfile):
    re_iteration = re.compile(r'At iteration (\d+)/(\d+)/(\d+)')
    re_bcer_train = re.compile(r'BCER train=([0-9.e+-]+)')
    re_stage = re.compile(r'stage (\d+)')
    re_bcer_eval = re.compile(
        r'At iteration (\d+), stage (\d+), BCER eval=([0-9.e+-]+)')
    find_subtrainer = 'Sub'
    find_checkpoint = 'wrote best model'

    iteration_line = ([], [], [])
    checkpoint_line = ([], [], [])
    subtrainer_line = ([], [], [])
    eval_line = ([], [])

    lines = []
    with open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
        for ln in f:
            if ln.startswith('At iteration') or ln.startswith('UpdateSubtrainer') or ln.startswith('Sub'):
                lines.append('\n')
            if len(ln) > 70:
                lines.append(ln.rstrip('\r\n'))
            else:
                lines.append(ln)
    text = ''.join(lines)

    for ln in text.split('\n'):
        stage = None
        bcer_eval = None
        match = re_bcer_eval.search(ln)
        if match:
            learning_iteration = int(match.group(1))
            stage = int(match.group(2))
            bcer_eval = float(match.group(3))
            eval_line[0].append(bcer_eval)
            eval_line[1].append(learning_iteration)
        match = re_iteration.search(ln)
        if match is None:
            continue
        learning_iteration = int(match.group(1))
        training_iteration = int(match.group(2))
        sample_iteration = int(match.group(3))
        match = re_bcer_train.search(ln)
        if match is None:
            continue
        bcer_train = float(match.group(1))
        match = re_stage.search(ln)
        if match:
            stage = int(match.group(1))
        subtrainer = (find_subtrainer in ln)
        checkpoint = (find_checkpoint in ln)
        if find_subtrainer in ln:
            subtrainer_line[0].append(bcer_train)
            subtrainer_line[1].append(learning_iteration)
            subtrainer_line[2].append(training_iteration)
        else:
            iteration_line[0].append(bcer_train)
            iteration_line[1].append(learning_iteration)
            iteration_line[2].append(training_iteration)
        if find_checkpoint in ln:
            checkpoint_line[0].append(bcer_train)
            checkpoint_line[1].append(learning_iteration)
            checkpoint_line[2].append(training_iteration)
    return iteration_line, checkpoint_line, subtrainer_line, eval_line


def plot(logfile, plotfile, model_name='model'):
    maxticks = 10

    (y, x, t), (c, cx, ct), (s, sx, st), (e, ex) = parse_tesseract_log5(logfile)
    x = np.array(x)
    y = np.array(y)

    def annot_min(boxcolor, xpos, ypos, x, y, z):
        if not z:
            xmin = x[np.argmin(y)]
            ymin = np.min(y)
            boxtext= "{:.3f}% BCER at\n {:,} learning iterations" .format(ymin,xmin)
        else:
            tmin = z[np.argmin(y)]
            xmin = x[np.argmin(y)]
            ymin = np.min(y)
            boxtext= "{:.3f}% BCER at\n  {:,} learning iterations\n  {:,} training iterations" .format(ymin,xmin,tmin)
        ax1.annotate(boxtext, xy=(xmin, ymin), xytext=(xpos,ypos), textcoords='offset points', color='black', fontweight = 'bold',
            arrowprops=dict(shrinkA=1, shrinkB=1, fc=boxcolor,alpha=0.7, ec='white', connectionstyle="arc3"),
            bbox=dict(boxstyle='round,pad=0.2', fc=boxcolor, alpha=0.3))

    PlotTitle="Tesseract LSTM Training - " + model_name
    fig = plt.figure(figsize=(11,8.5)) #size is in inches
    ax1 = fig.add_subplot()

    ax1.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax1.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.1f"))
    ax1.set_ylabel('BCER Character Error Rate %')

    ax1.set_xlabel('Learning Iterations')
    ax1.set_xticks(x)
    ax1.tick_params(axis='x', labelsize='small')
    ax1.locator_params(axis='x', nbins=maxticks)  # limit ticks on x-axis
    ax1.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax1.xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))

    ax1.scatter(x, y, c='teal', alpha=0.7, s=0.5, label='BCER every 100 Training Iterations')
    ax1.plot(x, y, 'teal', alpha=0.3, linewidth=0.5, label='Training BCER')
    ax1.grid(True)

    if s: # not NaN or empty
        ax1.plot(sx, s, 'orange', linewidth=0.2, label='SubTrainer BCER')
        ax1.scatter(sx, s, c='orange', s=0.5,
           label='BCER for UpdateSubtrainer:Sub every 100 iterations', alpha=0.5)
        annot_min('orange',-40,-40,sx,s,st)

    if e: # not NaN or empty
        ax1.plot(ex, e, 'magenta', linewidth=1.0)
        ax1.scatter(ex, e, c='magenta', s=30,
           label='BCER from evaluation during training', alpha=0.5)
        annot_min('magenta',-50,50,ex,e,[])

    if c: # not NaN or empty
    #    ax1.plot(ct, c, 'blue', linewidth=1.0)
        ax1.scatter(cx, c, c='blue', s=15,
           label='BCER at Checkpoints during training', alpha=0.5)
        annot_min('blue',-100,-100,cx,c,ct)

    tmax = t[np.argmax(x)]
    ymax = y[np.argmax(x)]
    xmax = np.max(x)
    boxtext= "{:.3f}% BCER at\n  {:,} learning iterations\n  {:,} training iterations" .format(ymax,xmax,tmax)
    ax1.annotate(boxtext, xy=(xmax, ymax), xytext=(5,-20), textcoords='offset points', color='black',
                bbox=dict(boxstyle='round,pad=0.2', fc='teal', alpha=0.3))
            
    plt.title(label=PlotTitle,  fontsize = 14, fontweight = 'bold')
    plt.legend(loc='upper right')

    ymaxcer = max(1.5, min(100.5, np.quantile(y, 0.5) * 3))

    ax1.set_ylim([-0.5, ymaxcer])

    # Secondary x axis on top to display Training Iterations
    ax2 = ax1.twiny() # ax1 and ax2 share y-axis
    ax2.set_xlabel("Training Iterations")
    ax2.set_xlim(ax1.get_xlim()) # ensure the independant x-axes now span the same range
    ax2.set_xticks(x) # copy over the locations of the x-ticks from Learning Iterations
    ax2.tick_params(axis='x', labelsize='small')
    ax2.set_xticklabels(matplotlib.ticker.StrMethodFormatter('{x:,.0f}').format_ticks(t)) # But give value of Training Iterations
    ax2.locator_params(axis='x', nbins=maxticks)  # limit ticks to same as x-axis
    ax2.xaxis.set_ticks_position('bottom') # set the position of ticks of the second x-axis to bottom
    ax2.xaxis.set_label_position('bottom') # set the position of labels of the second x-axis to bottom
    ax2.spines['bottom'].set_position(('outward', 36)) # positions the second x-axis below the first x-axis

    plt.savefig(plotfile)


def main():
    arg_parser = argparse.ArgumentParser(
        '''Creates plot from Training and Evaluation Character Error Rates''')
        
    arg_parser.add_argument(
        '-m', '--model', nargs='?', metavar='MODEL_NAME', help='Model Name')
                            
    arg_parser.add_argument(
        'logfile', help='Tesseract log file name')

    arg_parser.add_argument(
        'chartfile', help='Output chart file name (png)')

    args = arg_parser.parse_args()

    model_name = args.model or os.path.basename(os.path.dirname(
        os.path.abspath(args.logfile)))

    plotfile = args.chartfile or ('%s.png' % model_name)
    plot(args.logfile, plotfile, model_name)


if __name__ == '__main__':
    main()
