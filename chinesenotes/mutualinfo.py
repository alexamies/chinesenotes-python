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
Derives mutual information of multi-character terms from term and char info.
"""

import argparse
import codecs
import logging
import math


def ComputeMutualInfo(char_freq_file, term_freq_file, output_file, filter_file):
  """Computes mutual information of multi-character terms

  Use the corpus term and character frequency information to compute the mutual
  information for each term, compared to the characters being placed randomly
  next to each other. The frequency files are those produced by the charcount.py
  and term_frequency.py in this repo.
  """
  logging.info('ComputeMutualInfo: {}, {}'.format(char_freq_file,
                                                  term_freq_file))
  (char_freq, char_count) = load_freq(char_freq_file)
  (term_freq, term_count) = load_freq(term_freq_file)
  filter_freq = None
  if filter_file:
    (filter_freq, filter_count) = load_freq(filter_file)
  if char_count == 0 or term_count == 0:
    logging.error('ComputeMutualInfo: count is zero: {}, {}'.format(char_count,
                                                                    term_count))
    return
  mi = {}
  for term in term_freq:
    pc = 1.0
    if len(term) > 1:
      for c in term:
        if c in char_freq:
          pc *= char_freq[c] / char_count
      pt = term_freq[term] / term_count
      if not filter_freq and pc > 0.0:
        # No filtering, write all terms
        mi[term] = math.log(2, pt / pc)
      elif filter_freq and term in filter_freq and pc > 0.0:
        # Restrict to filtered terms
        mi[term] = math.log(2, pt / pc)
  write_mi(output_file, mi)


def load_freq(fname):
  """Reads the frequency distribution from a TSV file
  """
  dist = {}
  count = 0
  with codecs.open(fname, 'r', 'utf-8') as f:
    for line in f:
      fields = line.split('\t')
      if len(fields) > 1:
        key = fields[0]
        val = int(fields[1])
        dist[key] = val
        count += val
  logging.info('load_freq: {} entries loaded from {}'.format(len(dist), fname))
  return (dist, count)

def write_mi(fname, mi):
  """Writes the mutual informaiton distribution to the TSV output file
  """
  logging.info('write_mi: writing {} terms'.format(len(mi)))
  count = 0
  with codecs.open(fname, 'w', 'utf-8') as f:
    for t in mi:
      f.write('{}\t{}\n'.format(t, mi[t]))

# For use from command line
def main():
  logging.basicConfig(level=logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--char_freq_file',
                      dest='char_freq_file',
                      required=True,
                      help='Character frequency file')
  parser.add_argument('--term_freq_file',
                      dest='term_freq_file',
                      required=True,
                      help='Term frequency file')
  parser.add_argument('--output_file',
                      dest='output_file',
                      required=True,
                      help='Output file to write results to')
  parser.add_argument('--filter_file',
                      dest='filter_file',
                      required=True,
                      help='Filter file to restrict results to')
  args = parser.parse_args()
  ComputeMutualInfo(args.char_freq_file,
                    args.term_freq_file,
                    args.output_file,
                    args.filter_file)


if __name__ == "__main__":
  main()