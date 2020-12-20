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
Plot the results of processing the annotated corpus file
"""

import argparse
import codecs
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from numpy import random 


def PlotResults(infile, outfile, decision_point):
  """Plots data

  Args:
    infile: input file with the data to plot
    outfile: output file to write chart to
    decision_point: (optional) Decision point (mutual information) to plot
  """
  print('Plotting results')
  x1, x2, y = load_training_data(infile)
  print('Loaded {} points'.format(len(x1)))
  # All points
  colors = []
  x_fn_jitter = []
  for i in range(len(y)):
    c = 'g'
    if y[i] == 0:
      c = 'r'
    colors.append(c)
    new_val = x2[i] + random.normal(0.0, 0.025)
    x_fn_jitter.append(new_val)
  #plt.figure(num=None, figsize=(4, 6))
  plt.subplot(121)
  plt.scatter(x_fn_jitter, x1, c=colors, s=25, marker='^')
  if decision_point:
    xd = [-0.1, 1.1]
    yd = [decision_point, decision_point]
    plt.plot(xd, yd, color='blue')
  plt.title('All Predictions')
  plt.xlabel('Contains Function Word')
  plt.ylabel('Mutual Information')
  plt.xticks([0, 1], ('False', 'True')) 
  plt.ylim([-3, 20])
  green_data = mpatches.Patch(color='green', label='Correct')
  red_data = mpatches.Patch(color='red', label='Incorrect')
  blue_data = mpatches.Patch(color='blue', label='Decision boundary')
  plt.legend(handles=[green_data, red_data, blue_data])
  # Only incorrect values
  plt.subplot(122)
  colors = []
  x_mi = []
  x_fn = []
  y_incorrect = []
  for i in range(len(y)): 
    if y[i] == 0:
      x_mi.append(x1[i])
      new_val = x2[i] + random.normal(0.0, 0.025)
      x_fn.append(new_val)
      colors.append('r')
  plt.scatter(x_fn, x_mi, c=colors, s=25, marker='^')
  plt.title('Incorrect Predictions')
  plt.xlabel('Contains Function Word')
  plt.xticks([0, 1], ('False', 'True')) 
  plt.ylim([-3, 20])
  #plt.show()
  plt.savefig(outfile)


def load_training_data(infile):
  x1 = []
  x2 = []
  y = []
  with codecs.open(infile, 'r', "utf-8") as f:
    for line in f:
      line = line.strip()
      if line.startswith('#'):
        continue
      fields = line.split('\t')
      if len(fields) > 3:
        term = fields[0]
        mi = float(fields[1])
        has_fn = float(fields[2])
        result = int(fields[3])
        x1.append(mi)
        x2.append(has_fn)
        y.append(result)
  return (x1, x2, y)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--infile',
                      dest='infile',
                      help='File name to process')
  parser.add_argument('--outfile',
                      dest='outfile',
                      help='File name to write chart to')
  parser.add_argument('--decision_point',
                      dest='decision_point',
                      type=float,
                      required=False,
                      help='Decision point (mutual information)')
  args = parser.parse_args()
  PlotResults(args.infile, args.outfile, args.decision_point)


# Entry point from a script
if __name__ == "__main__":
  main()