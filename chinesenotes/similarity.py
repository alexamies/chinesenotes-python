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
Methods for computing similarity of strings of Chinese characters
"""

import argparse
import logging
import os
from typing import List, Mapping

from chinesenotes import cndict
from chinesenotes.cndict_types import DictionaryEntry


def hamming_distance(w1: str, w2: str)->int:
  """Compute the hamming distance between the given strings"""
  d = 0
  for i in range(len(w1)):
    if i >= len(w2):
      return d
    if w1[i] != w2[i]:
      d += 1
  return d


def num_same_chars(w1: str, w2: str)->int:
  """Compute the similarity of two strings based on the number of matching characters"""
  sim = 0
  for ch in w1:
    if ch in w2:
      sim += 1
  return sim


def find_similar(w: str,
    wdict: Mapping[str, DictionaryEntry])->List[str]:
  """Finds the most similar words in the dictionary based on multiple measures"""
  most_similar = find_similar_hamming(w, wdict)
  most_similar_chars = find_similar_same_chars(w, wdict)
  most_similar.extend(most_similar_chars)
  return most_similar


def find_similar_hamming(w: str,
    wdict: Mapping[str, DictionaryEntry])->List[str]:
  """Finds the most similar words based on Hamming distance"""
  d_min = 100
  most_similar = []
  for key in wdict:
    d = hamming_distance(w, key)
    if d < d_min: # new min
      d_min = d
      most_similar.append(key)
    elif d == d_min: # tie
      most_similar = [key]
  return most_similar


def find_similar_same_chars(w: str,
    wdict: Mapping[str, DictionaryEntry])->List[str]:
  """Finds the most similar words based on number of same characters"""
  sim_max = 0
  most_similar = []
  for key in wdict:
    sim = num_same_chars(w, key)
    if sim > sim_max: # new max
      sim_max = sim
      most_similar.append(key)
    elif sim == sim_max: # tie
      most_similar = [key]
  logging.info(f'find_similar_same_chars, sim_max: {sim_max}, most_similar: {most_similar}')
  return most_similar


def main():
  """Command line entry point"""
  logging.basicConfig(level=logging.INFO)
  cn_home = 'https://github.com/alexamies/chinesenotes.com'
  fname = f'{cn_home}/blob/master/data/words.txt?raw=true'
  wdict = {}
  if 'CNREADER_HOME' in os.environ:
    cn_home = os.environ['CNREADER_HOME']
    fname = f'{cn_home}/data/words.txt'
  parser = argparse.ArgumentParser()
  parser.add_argument('--word',
                      dest='word',
                      help='Target to search for similar terms')
  args = parser.parse_args()
  if not args.word:
    print('Please supply target word with --word')
    return
  cnotes_dict = cndict.open_dictionary()
  most_similar = find_similar(args.word, cnotes_dict)
  logging.info(f'Words most similar to {args.word}: {most_similar}')

# Entry point from a script
if __name__ == '__main__':
  main()
