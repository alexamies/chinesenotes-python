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
from sklearn.metrics import classification_report
from sklearn.tree import export_graphviz


INFILE_DEF = 'data/phrase_similarity_combined.csv'
OUTFILE_DEF = 'drawings/phrase_similarity_graph.png'


def run(infile, outfile, val_file):
  """Load training data and train the classifier

  Args:
    infile: input file with the mutual information and training points
    outfile: file name to write graphviz export to
  """
  x, y = load_training2(infile)
  feature_names = ['Unigram count / len', 'Hamming distance / len']
  train(x, y, feature_names, outfile)
  x, y = load_training3(infile)
  feature_names = ['Unigram count', 'Hamming distance', 'Query length']
  clf = train(x, y, feature_names, outfile)
  if len(val_file) > 0:
    x, y = load_training3(val_file)
    validate(clf, x, y, feature_names)


def train(x, y, feature_names, outfile):
  """Train the classifier

  Args:
    x: list of values for feature variables
    y: list of target values
    feature_names: Names of feature variables
    outfile: file name to write graphviz export to
  Returns:
    the trained classifier
  """
  clf = tree.DecisionTreeClassifier(random_state=0,
                                    max_depth=2,
                                    criterion='gini',
                                    min_samples_split=3)
  clf = clf.fit(x, y)
  score = clf.score(x, y)
  logging.info(f'Classifier score: {score}\n')
  y_pred = clf.predict(x)
  print("Training results")
  print(classification_report(y, y_pred))
  dot_data = tree.export_graphviz(clf, filled = True, rounded = True)
  graph = graphviz.Source(dot_data) 
  class_names = ['Not relevant', 'Relevant']
  r = tree.export_text(clf, feature_names=feature_names)
  print(r)
  tree.plot_tree(clf,
                 feature_names=feature_names,
                 class_names=class_names,
                 filled=True, 
                 impurity=False)
  #plt.show()
  plt.savefig(outfile, dpi=160)
  return clf


def validate(clf, x, y, feature_names):
  """Validate the classifier

  Args:
    x: list of values for feature variables
    y: list of target values
    feature_names: Names of feature variables
  """
  y_pred = clf.predict(x)
  print("Validation results")
  print(classification_report(y, y_pred))


def load_training2(infile):
  """Load training data with normalized unigram count and hamming distance.

  Args:
    infile: file name to load data from
  """
  X = []
  Y = []
  with open(infile, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
      if reader.line_num == 1:  # Skip header row
        continue
      if len(row) > 8:
        query = row[0]
        unigram_count = float(row[5]) / len(query)
        hamming = float(row[6]) / len(query)
        relevance = int(row[8])
        x = [unigram_count, hamming]
        X.append(x)
        Y.append(relevance)
  return (X, Y)

def load_training3(infile):
  """Load training data with normalized unigram count, hamming distance, and 
     query length.

  Args:
    infile: file name to load data from
  """
  X = []
  Y = []
  with open(infile, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
      if reader.line_num == 1:  # Skip header row
        continue
      if len(row) > 8:
        query = row[0]
        unigram_count = int(row[5])
        hamming = int(row[6])
        relevance = int(row[8])
        x = [unigram_count, hamming, len(query)]
        X.append(x)
        Y.append(relevance)
  return (X, Y)

def main():
  logging.basicConfig(level=logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--infile',
                      dest='infile',
                      default=INFILE_DEF, 
                      help='File name to read training data from')
  parser.add_argument('--outfile',
                      dest='outfile',
                      default=OUTFILE_DEF, 
                      help='File name to write output to')
  parser.add_argument('--valfile',
                      dest='valfile',
                      default="", 
                      help='File name to read validation data from')
  args = parser.parse_args()
  logging.info(f'Training decision tree from {args.infile}, output to {args.outfile}')
  run(args.infile, args.outfile, args.valfile)


# Entry point from a script
if __name__ == "__main__":
  main()