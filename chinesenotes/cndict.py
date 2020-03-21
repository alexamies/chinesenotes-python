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
Utility loads the Chinese Notes Reader dictionary into a Python dictionary.

Simplified and traditional words are keys.
"""
import argparse
import logging
import os
import urllib.request
from typing import List, Mapping, TextIO

from chinesenotes.config import AppConfig
from chinesenotes.config import ConfigException
from chinesenotes.cndict_types import DictionaryEntry
from chinesenotes.cndict_types import WordSense


def lookup(wdict: Mapping[str, DictionaryEntry],
           keyword: str) -> DictionaryEntry:
  """Looks up the keyword in the dictionary or return None if it is not there
  """
  return wdict[keyword]


def open_dictionary(fname=None,
                    chinese_only=False) -> Mapping[str, DictionaryEntry]:
  """Reads the dictionary from a file or URL.

    Set chinese_only = True if you are only using the dictionary to segment
    Chinese text. This will decrease the memory needed.

    Args:
      fname: the file or remote URL to read the dictionary from
      chinese_only: Only include Chinese and no other fields
    Returns:
      A dictionary object
  """
  print(f'Opening the Chinese Notes dictionary from {fname}')
  wdict = {}
  if fname and fname.startswith('https'): # Download from GitHub
    wdict = _load_from_url(fname, chinese_only)
  elif fname: # Load with given file name
    wdict = _load_locally(fname, chinese_only)
  elif not fname and 'CNREADER_HOME' in os.environ: # Load based on app config
    app_config = AppConfig()
    app_config.load()
    wdict = _load_dict_files(app_config.lex_unit_files, chinese_only)
  else:
    raise ConfigException('No parametrs provided to load dictionary')
  print(f'open_dictionary completed with {len(wdict)} entries"')
  return wdict


def tokenize_greedy(wdict: Mapping[str, DictionaryEntry],
                    chunk: str) -> List[str]:
  """A greedy tokenizer"""
  segments = []
  i = 0
  while i < len(chunk):
    for j in range(len(chunk), -1, -1):
      word = chunk[i:j]
      if word in wdict:
        segments.append(word)
        i += len(word)
        break
      if len(word) == 1:
        segments.append(word)
        i += 1
        break
  return segments

def tokenize_exclude_whole(wdict: Mapping[str, DictionaryEntry],
                    chunk: str) -> List[str]:
  """A tokenize but not including the full word"""
  segments = []
  i = 0
  while i < len(chunk):
    for j in range(len(chunk), -1, -1):
      word = chunk[i:j]
      if word in wdict and not word == chunk:
        segments.append(word)
        i += len(word)
        break
      if len(word) == 1:
        segments.append(word)
        i += 1
        break
  return segments


def _load_dictionary(dict_file: TextIO,
                     chinese_only=False) -> Mapping[str, DictionaryEntry]:
  """Loads the dictionary from a file or URL.

    Set chinese_only = True if you are only using the dictionary to segment
    Chinese text. This will decrease the memory needed.

    Args:
      fname: the file or remote URL to read the dictionary from
      chinese_only: Only include Chinese and no other fields
    Returns:
      A dictionary of DictionaryEntry objects
  """
  wdict = {}
  for line in dict_file:
    line = line.strip()
    if not line:
      continue
    fields = line.split('\t')
    if fields and len(fields) >= 10:
      traditional = fields[2]
      simplified = fields[1]
      pinyin = None
      english = None
      grammar = None
      notes = None
      headword_id = None
      if not chinese_only:
        pinyin = fields[3]
        english = fields[4]
        grammar = fields[5]
        if len(fields) >= 14 and fields[14] != '\\N':
          notes = fields[14]
        if fields and len(fields) >= 15 and fields[15] != '\\N':
          headword_id = fields[15]
      sense = WordSense(simplified, traditional, pinyin, english)
      if grammar:
        sense.grammar = grammar
      if notes:
        sense.notes = notes
      key = simplified
      if key not in wdict:
        entry = DictionaryEntry(simplified, [sense], headword_id)
        wdict[key] = entry
      else:
        # Entry is in dict, append the word sense
        entry = wdict[key]
        entry.add_word_sense(sense)
      if traditional != '\\N' and traditional not in wdict:
        # Also index by traditional
        entry = DictionaryEntry(traditional, [sense], headword_id)
        wdict[traditional] = entry
      elif traditional != '\\N':
        entry = wdict[traditional]
        entry.add_word_sense(sense)
  return wdict

def _load_dict_files(dict_files: List[str],
                     chinese_only=False) -> Mapping[str, DictionaryEntry]:
  """Loads the dictionary from a file or URL.

    Set chinese_only = True if you are only using the dictionary to segment
    Chinese text. This will decrease the memory needed.

    Args:
      fname: the file or remote URL to read the dictionary from
      chinese_only: Only include Chinese and no other fields
    Returns:
      A dictionary of DictionaryEntry objects
  """
  wdict = {}
  for fname in dict_files:
    term_dict = _load_locally(fname, chinese_only)
    if not wdict:
      wdict = term_dict
    else:
      for key, entry in term_dict.items():
        if entry not in wdict:
          wdict[key] = entry
        else:
          for sense in entry.senses:
            wdict[key].add_word_sense(sense)
  return wdict

def _load_from_url(url: str,
                   chinese_only=False) -> Mapping[str, DictionaryEntry]:
  """Reads the dictionary from a local file
  """
  logging.info('Opening the dictionary remotely')
  with urllib.request.urlopen(url) as dict_file:
    data = dict_file.read().decode('utf-8')
    return _load_dictionary(data.splitlines(), chinese_only)

def _load_locally(fname: str,
                  chinese_only=False) -> Mapping[str, DictionaryEntry]:
  """Reads the dictionary from a local file
  """
  logging.info(f'Opening dictionary from local file {fname}')
  with open(fname, 'r') as dict_file:
    return _load_dictionary(dict_file, chinese_only)


def main():
  """Command line entry point"""
  logging.basicConfig(level=logging.INFO)
  cn_home = 'https://github.com/alexamies/chinesenotes.com'
  fname = f'{cn_home}/blob/master/data/words.txt?raw=true'
  wdict = {}
  if 'CNREADER_HOME' in os.environ:
    cn_home = os.environ['CNREADER_HOME']
    fname = f'{cn_home}/data/words.txt'
  wdict = open_dictionary(fname)
  parser = argparse.ArgumentParser()
  parser.add_argument('--lookup',
                      dest='lookup',
                      help='Lookup a word')
  parser.add_argument('--tokenize',
                      dest='tokenize',
                      help='Segment the text into multi-character terms')
  args = parser.parse_args()
  if args.lookup:
    entry = lookup(wdict, args.lookup)
    senses = entry.senses
    if not senses:
      print(f'entry has no word senses: {entry}')
    english = senses[0].english
    print(f'English: {english}')
  elif args.tokenize:
    logging.info('Greedy dictionary-based text segmentation')
    segments = tokenize_greedy(wdict, args.tokenize)
    print(f'Segments: {segments}')

# Entry point from a script
if __name__ == '__main__':
  main()
