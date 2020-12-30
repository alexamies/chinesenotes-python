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


INFILE_DEF = 'data/phrase_similarity_training.csv'
OUTFILE_DEF = 'drawings/phrase_similarity_plot.png'
UNIGRAM_DEF = 0.46
HAMMING_DEF = 0.63

def PlotResults(infile: str, outfile: str, unigram_lim: float,
                hamming_lim: float):
  """Plots data

  Args:
    infile: input file with the data to plot
    outfile: output file to write chart to
  """
  x1, x2, y = load_training_data(infile)
  print(f'Loaded {len(x1)} points')
  # All points
  colors = []
  x_fn_jitter = []
  y_fn_jitter = []
  for i in range(len(y)):
    c = 'g'
    if y[i] == 0:
      c = 'r'
    colors.append(c)
    new_xval = x1[i] + random.normal(0.0, 0.01)
    x_fn_jitter.append(new_xval)
    new_yval = x2[i] + random.normal(0.0, 0.01)
    y_fn_jitter.append(new_yval)
  #plt.figure(num=None, figsize=(4, 6))
  #plt.subplot(121)
  plt.scatter(x_fn_jitter, y_fn_jitter, c=colors, s=25, marker='^')
  xd = [-0.1, hamming_lim, hamming_lim]
  yd = [unigram_lim, unigram_lim, 1.0]
  plt.plot(xd, yd, color='blue')
  plt.title('Phrase similarity relevance')
  plt.xlabel('Hamming distance / len')
  plt.ylabel('Unigram count / len')
  # plt.xticks([0, 1], ('False', 'True')) 
  plt.xlim([0.0, 1.0])
  plt.ylim([0.0, 1.0])
  green_data = mpatches.Patch(color='green', label='Relevant')
  red_data = mpatches.Patch(color='red', label='Not relevant')
  blue_data = mpatches.Patch(color='blue', label='Decision boundary')
  plt.legend(handles=[green_data, red_data, blue_data])
  #plt.show()
  plt.savefig(outfile)


def load_training_data(infile):
  """Loads the training data from the given CSV file."""
  x1 = []
  x2 = []
  y = []
  with open(infile, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
      if reader.line_num == 1:  # Skip header row
        continue
      if len(row) > 8:
        query = row[0]
        unigram_count = int(row[5]) / (len(query) * 1.0)
        hamming = float(row[6]) / (len(query) * 1.0)
        relevance = int(row[8])
        x1.append(hamming)
        x2.append(unigram_count)
        y.append(relevance)
      else:
        log(f'Could not understand row {row}')
  return (x1, x2, y)


def main():
  logging.basicConfig(level=logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--infile',
                      dest='infile',
                      default=INFILE_DEF, 
                      help='File name to read infile from')
  parser.add_argument('--outfile',
                      dest='outfile',
                      default=OUTFILE_DEF, 
                      help='File name to save plot to')
  parser.add_argument('--unigram_lim',
                      dest='unigram_lim',
                      default=UNIGRAM_DEF,
                      type=float,
                      help='Unigram frequency decision boundary')
  parser.add_argument('--hamming_lim',
                      dest='hamming_lim',
                      default=HAMMING_DEF, 
                      type=float,
                      help='Hamming distance decision boundary')
  args = parser.parse_args()
  logging.info(f'Plotting results from {args.infile} to {args.outfile}')
  PlotResults(args.infile, args.outfile, args.unigram_lim, args.hamming_lim)


# Entry point from a script
if __name__ == "__main__":
  main()
