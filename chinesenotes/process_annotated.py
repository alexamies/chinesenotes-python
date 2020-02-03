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
Process an annotated corpus file of tokenization results.

Computes recall and precession and writes out a training set for filtering of
two character terms.
"""

import argparse
import codecs
import re

punctuation = set([u'，', u'；', u'。', u'、', u'(', u')'])
error_pattern = re.compile(r'Error: (.*) \(')
function_words = set([u'有', u'不', u'無', u'下', u'上', u'為', u'後'])

def Process(fname, mutual_info_file, outfile):
  """Process the file

  Args:
    fname: input file with the annotated tokenization corpus
    mutual_info: input file with the mutual information
    outfile: output file with the filter training results for two-character
    terms.
  """
  tp = 0
  fn = 0
  fp = 0
  terms = {}
  pattern = re.compile(r'^[#|Note|Source|Translation|Error]')
  p = re.compile(r'、')
  with codecs.open(fname, 'r', "utf-8") as f:
    for line in f:
      line = line.strip()
      if line != '' and pattern.match(line) == None:
        tokens = p.split(line)
        i = 0
        for t in tokens:
          if t.strip() != '':
            i += 1
            term = strip_punctuation(t)
            terms[term] = 1
        tp += i
      if line.startswith('Error'):
        if 'false negative' in line:
          fn += 1
        if 'false positive' in line:
          fp += 1
          term = find_term(line)
          terms[term] = 0
          print("False positive: {}".format(line))
  recall = tp / (tp + fn)
  precision = tp / (tp + fp)
  print("Tokens: {}".format(tp))
  print("False negatives: {}".format(fn))
  print("False positives: {}".format(fp))
  print("Recall: {0:.4g}".format(recall))
  print("Precision: {0:.4g}".format(precision))
  write_training(mutual_info_file, outfile, terms)


def find_term(line):
  """Extracts the term from a line from an error line"""
  m = error_pattern.match(line)
  return m.group(1)

def includes_function_word(term):
  """1 if any of the characters are function words"""
  for c in term:
    if c in function_words:
      return 1
  return 0

def read_mutual_info(fname):
  """Reads mutual_info from a file into a dictionary

  Args:
    fname: the file name
  Returns:
    A dictionary with the mutual information
  """
  mutual_info = {}
  with codecs.open(fname, 'r', "utf-8") as f:
    for line in f:
      line = line.strip()
      fields = line.split('\t')
      if len(fields) > 1:
        term = fields[0]
        mi =fields[1]
        mutual_info[term] = mi
  return mutual_info

def strip_punctuation(term):
  """Strips punctuation"""
  t = u""
  for c in term:
    if c not in punctuation:
      t += c
  return t

def write_training(mutual_info_file, outfile, terms):
  """Writes training data for each term in terms to the output file"""
  mutual_info = read_mutual_info(mutual_info_file)
  with codecs.open(outfile, 'w', "utf-8") as f:
    f.write('#Term\tMutual Info\tIncludes Fn Words\tResult\n')
    for t in terms.keys():
      if len(t) == 2:
        if t in mutual_info:
          mi = mutual_info[t]
          has_fn = includes_function_word(t)
          result = terms[t]
          f.write('{}\t{}\t{}\t{}\n'.format(t, mi, has_fn, result))
        else:
          print('Mutual info not found for {}\n'.format(t))

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--filename',
                      dest='filename',
                      help='File name to process')
  parser.add_argument('--mutual_info',
                      dest='mutual_info',
                      help='File name with pointwise mutual information')
  parser.add_argument('--outfile',
                      dest='outfile',
                      help='File name to write results to')
  args = parser.parse_args()
  Process(args.filename, args.mutual_info, args.outfile)


# Entry point from a script
if __name__ == "__main__":
  main()