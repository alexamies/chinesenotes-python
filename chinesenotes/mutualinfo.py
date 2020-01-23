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
Derives mutual information of two-character terms from bigram and char info.
"""

import argparse
import codecs
import logging
import math


def ComputeMutualInfo(char_freq_file, bi_freq_file, output_file, filter_file):
  """Computes mutual information of multi-character terms

  Use the corpus character and character bigram frequency information to compute
  the mutual information for each bigram, compared to the characters being
  placed randomly next to each other. The frequency files are those produced by
  the charcount.py and char_bigram_count.py programs in this repo.
  The list are filtered by dictionary terms from the term_frequency.py
  program in this repo.
  """
  logging.info('ComputeMutualInfo: {}, {}'.format(char_freq_file,
                                                  bi_freq_file))
  (char_freq, char_count) = load_freq(char_freq_file)
  (bigram_freq, bigram_count) = load_freq(bi_freq_file)
  (filter_freq, filter_count) = load_freq(filter_file)
  if char_count == 0 or bigram_count == 0:
    logging.error('ComputeMutualInfo: count zero: {}, {}'.format(char_count,
                                                                 bigram_count))
    return
  mi = {}
  for term in filter_freq:
    pc = 1.0
    # Only compute mutual information for two-character terms
    if len(term) == 2:
      c1 = term[0]
      c2 = term[1]
      if c1 in char_freq and c2 in char_freq:
          pc = (char_freq[c1] * char_freq[c2]) / (char_count * char_count)
      b1 = '{}{}'.format(c1, c2)
      fb1 = 0
      if b1 in bigram_freq:
          fb1 = bigram_freq[b1]
      b2 = '{}{}'.format(c2, c1)
      fb2 = 0
      if b2 in bigram_freq and b1 != b2:
          fb2 = bigram_freq[b2]
      pb = (fb1 + fb2) / bigram_count
      if pb > 0 and pc > 0:
        mi[term] = math.log(pb / pc, 2)
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
  logging.info('load_freq: {} count loaded from {}'.format(count, fname))
  return (dist, count)

def write_mi(fname, mi):
  """Writes the mutual informaiton distribution to the TSV output file
  """
  with codecs.open(fname, 'w', 'utf-8') as f:
    for t in mi:
      f.write('{}\t{}\n'.format(t, mi[t]))
  logging.info('wrote {} terms to {}'.format(len(mi), fname))

# For use from command line
def main():
  logging.basicConfig(level=logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--char_freq_file',
                      dest='char_freq_file',
                      required=True,
                      help='Character frequency file')
  parser.add_argument('--bigram_freq_file',
                      dest='bigram_freq_file',
                      required=True,
                      help='Character bigram frequency file')
  parser.add_argument('--filter_file',
                      dest='filter_file',
                      required=True,
                      help='Filter file to restrict results to')
  parser.add_argument('--output_file',
                      dest='output_file',
                      required=True,
                      help='Output file to write results to')
  args = parser.parse_args()
  ComputeMutualInfo(args.char_freq_file,
                    args.bigram_freq_file,
                    args.output_file,
                    args.filter_file)


if __name__ == "__main__":
  main()