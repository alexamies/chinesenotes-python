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
Trains a decision tree classifier for phrase similarity.

Reads the input file and trains the classifier.
"""

import argparse
import csv
import logging
import graphviz
import matplotlib.pyplot as plt
from sklearn import tree
from sklearn.tree import export_graphviz


INFILE_DEF = 'data/phrase_similarity_training.csv'
OUTFILE_DEF = 'drawings/phrase_similarity_graph.png'

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
  feature_names = ['Unigram count / len', 'Hamming distance / len']
  class_names = ['Relevant', 'Not relevant']
  r = tree.export_text(clf, feature_names=feature_names)
  print(r)
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
  with open(infile, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
      if reader.line_num == 1:  # Skip header row
        continue
      if len(row) > 8:
        query = row[0]
        unigram_count = int(row[5])  / (len(query) * 1.0)
        hamming = float(row[6])  / (len(query) * 1.0)
        relevance = int(row[8])
        x = [unigram_count, hamming]
        X.append(x)
        Y.append(relevance)
  return (X, Y)

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
                      help='File name to write output to')
  args = parser.parse_args()
  logging.info(f'Training decision tree from {args.infile}, output to {args.outfile}')
  Train(args.infile, args.outfile)


# Entry point from a script
if __name__ == "__main__":
  main()