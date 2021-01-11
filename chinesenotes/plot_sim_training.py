# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Plot the similarity training results with unigram count and Hamming distance
"""

import argparse
import csv
import logging
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from numpy import random 
from chinesenotes import similarity_train


INFILE_DEF = 'data/phrase_similarity_training.csv'
OUTFILE_DEF2 = 'drawings/phrase_similarity_plot.png'
UNIGRAM_DEF2 = 0.41
HAMMING_DEF2 = 0.62
OUTFILE_DEF3 = 'drawings/phrase_similarity_plot3.png'
UNIGRAM_DEF3 = 3.0
HAMMING_DEF3 = 0.0

def run(infile: str, outfile: str, feature_names, unigram_lim: float,
                hamming_lim: float):
  """Load and plot data

  Args:
    infile: input file with the data to plot
    outfile: output file to write chart to
  """

def plot(x, y, outfile: str, feature_names, unigram_lim: float,
                hamming_lim: float, xlim: float, ylim: float, jitter: float):
  """Plots data

  Args:
    x: feature variables
    y: target variable
    outfile: output file to write chart to
  """
  # All points
  colors = []
  x0_fn_jitter = []
  x1_fn_jitter = []
  for i in range(len(y)):
    c = 'g'
    if y[i] == 0:
      c = 'r'
    colors.append(c)
    new_x0 = x[i][0] + random.normal(0.0, jitter)
    x0_fn_jitter.append(new_x0)
    new_x1 = x[i][1] + random.normal(0.0, jitter)
    x1_fn_jitter.append(new_x1)
  #plt.figure(num=None, figsize=(4, 6))
  #plt.subplot(121)
  plt.scatter(x1_fn_jitter, x0_fn_jitter, c=colors, s=25, marker='^')
  xd = [-0.1, hamming_lim, hamming_lim]
  yd = [unigram_lim, unigram_lim, ylim]
  plt.plot(xd, yd, color='blue',linewidth=1.0)
  plt.fill_between(x=[0, hamming_lim],
                   y1=[unigram_lim, unigram_lim],
                   y2=[ylim, ylim],
                   facecolor='lightgreen', alpha=0.2)
  plt.fill_between(x=[0, hamming_lim, hamming_lim, xlim],
                   y1=[0, 0, 0, 0],
                   y2=[unigram_lim, unigram_lim, ylim, ylim],
                   facecolor='lightcoral',
                   alpha=0.2)
  plt.title('Phrase similarity relevance')
  plt.xlabel(feature_names[1])
  plt.ylabel(feature_names[0])
  # plt.xticks([0, 1], ('False', 'True')) 
  plt.xlim([0.0, xlim])
  plt.ylim([0.0, ylim])
  green_data = mpatches.Patch(color='green', label='Relevant')
  red_data = mpatches.Patch(color='red', label='Not relevant')
  blue_data = mpatches.Patch(color='blue', label='Decision boundary')
  plt.legend(handles=[green_data, red_data, blue_data])
  # plt.show()
  plt.savefig(outfile)
  plt.close()

def main():
  logging.basicConfig(level=logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--infile',
                      dest='infile',
                      default=INFILE_DEF, 
                      help='File name to read infile from')
  parser.add_argument('--outfile2',
                      dest='outfile2',
                      default=OUTFILE_DEF2, 
                      help='File name to save 2 feature plot to')
  parser.add_argument('--outfile3',
                      dest='outfile3',
                      default=OUTFILE_DEF3, 
                      help='File name to save 3 feature plot to')
  parser.add_argument('--unigram_lim2',
                      dest='unigram_lim2',
                      default=UNIGRAM_DEF2,
                      type=float,
                      help='Unigram frequency (normalized) decision boundary')
  parser.add_argument('--unigram_lim3',
                      dest='unigram_lim3',
                      default=UNIGRAM_DEF3,
                      type=float,
                      help='Unigram frequency decision boundary')
  parser.add_argument('--hamming_lim2',
                      dest='hamming_lim2',
                      default=HAMMING_DEF2, 
                      type=float,
                      help='Hamming distance (normalized) decision boundary')
  parser.add_argument('--hamming_lim3',
                      dest='hamming_lim3',
                      default=HAMMING_DEF3, 
                      type=float,
                      help='Hamming distance decision boundary')
  args = parser.parse_args()
  logging.info(f'Plotting results from {args.infile} to {args.outfile2}')
  feature_names = ['Unigram count / len', 'Hamming distance / len']
  x2, y = similarity_train.load_training2(args.infile)
  print(f'Loaded {len(x2)} points')
  plot(x2, y, args.outfile2, feature_names, args.unigram_lim2, args.hamming_lim2, 1.0, 1.0, 0.01)

  x3, y = similarity_train.load_training3(args.infile)
  feature_names = ['Unigram count', 'Hamming distance', 'Query length']
  plot(x3, y, args.outfile3, feature_names, args.unigram_lim3, args.hamming_lim3, 4.0, 4.0, 0.03)


# Entry point from a script
if __name__ == "__main__":
  main()
