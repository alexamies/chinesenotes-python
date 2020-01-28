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
Process an annotated corpus file
"""

import argparse
import codecs
import re
import sys
import urllib.request


def Process(fname):
  """Process the file"""
  tp = 0
  fn = 0
  fp = 0
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
        tp += i
      if line.startswith('Error'):
        if 'false negative' in line:
          fn += 1
        if 'false positive' in line:
          fp += 1
  recall = tp / (tp + fn)
  precision = tp / (tp + fp)
  print("Tokens: {}".format(tp))
  print("False negatives: {}".format(fn))
  print("False positives: {}".format(fp))
  print("Recall: {0:.4g}".format(recall))
  print("Precision: {0:.4g}".format(precision))

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--filename',
                      dest='filename',
                      help='File name to process')
  args = parser.parse_args()
  Process(args.filename)

# Entry point from a script
if __name__ == "__main__":
  main()