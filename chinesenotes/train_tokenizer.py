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
Trains a decision tree classifier for a tokenization filer.

Reads the input file and trains the classifier.
"""

import argparse
import codecs
import graphviz
import matplotlib.pyplot as plt
from sklearn import tree
from sklearn.tree import export_graphviz

def Train(infile, outfile):
  """Train the classifier

  Args:
    infile: input file with the mutual information and training points
    outfile: file name to write graphviz export to
  """
  X, Y = load_training_data(infile)
  clf = tree.DecisionTreeClassifier(random_state=0,
                                    max_depth=2,
                                    criterion='gini',
                                    min_samples_split=3)
  clf = clf.fit(X, Y)
  dot_data = tree.export_graphviz(clf, filled = True, rounded = True)
  graph = graphviz.Source(dot_data) 
  feature_names = ['Mutual information', 'Has Function Word']
  class_names = ['Do not accept', 'Accept']
  tree.plot_tree(clf,
                 feature_names=feature_names,
                 class_names=class_names,
                 filled=True, 
                 impurity=False)
  #plt.show()
  plt.savefig(outfile, dpi=160)


def load_training_data(infile):
  X = []
  Y = []
  with codecs.open(infile, 'r', "utf-8") as f:
    for line in f:
      line = line.strip()
      if line.startswith('#'):
        continue
      fields = line.split('\t')
      if len(fields) > 3:
        term = fields[0]
        mi = float(fields[1])
        has_fn = int(fields[2])
        has_fn = False
        if int(fields[2]) == 1:
          has_fn = True
        y = int(fields[3])
        x = [mi, has_fn]
        X.append(x)
        Y.append(y)
  return (X, Y)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--infile',
                      dest='infile',
                      help='Training file name')
  parser.add_argument('--outfile',
                      dest='outfile',
                      help='File name to write graphviz export to')
  args = parser.parse_args()
  Train(args.infile, args.outfile)


# Entry point from a script
if __name__ == "__main__":
  main()