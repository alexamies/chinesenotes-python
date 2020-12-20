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

import csv
import logging
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from numpy import random 


def PlotResults(infile, outfile):
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
    new_xval = x2[i] + random.normal(0.0, 0.05)
    x_fn_jitter.append(new_xval)
    new_yval = x1[i] + random.normal(0.0, 0.05)
    y_fn_jitter.append(new_yval)
  #plt.figure(num=None, figsize=(4, 6))
  #plt.subplot(121)
  plt.scatter(x_fn_jitter, y_fn_jitter, c=colors, s=25, marker='^')
  xd = [-0.1, 5.5, 5.5, 7.1]
  yd = [1.5, 1.5, 2.5, 2.5]
  plt.plot(xd, yd, color='blue')
  plt.title('Phrase similarity relevance')
  plt.xlabel('Unigram count')
  plt.ylabel('Hamming distance')
  # plt.xticks([0, 1], ('False', 'True')) 
  # plt.ylim([-3, 20])
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
        unigram_count = int(row[5])
        hamming = float(row[6])
        relevance = int(row[8])
        x1.append(unigram_count)
        x2.append(hamming)
        y.append(relevance)
      else:
        log(f'Could not understand row {row}')
  return (x1, x2, y)


def main():
  logging.basicConfig(level=logging.INFO)
  infile = 'data/phrase_similarity_classified.csv'
  outfile = 'drawings/phrase_similarity_classified.png'
  logging.info(f'Plotting results from {infile} to {outfile}')
  PlotResults(infile, outfile)


# Entry point from a script
if __name__ == "__main__":
  main()
