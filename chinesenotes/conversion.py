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
Utilities for converting dictionary file
"""

import logging
import os
import re

from chinesenotes import charutil
from chinesenotes import cndict
from chinesenotes.cndict_types import DictionaryEntry
from chinesenotes.cndict_types import WordSense


# Download the file from
# https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip
DICT_FILE_NAME = '../cc-cedict/cedict_ts.u8'


class EntryAnalyzer:
  """Methods for analyzing entries"""
  def __init__(self):
    self.p_contains_alphanum = re.compile('[a-zA-Z0-9]+')

  def contains_alphanum(self, chinese: str) -> bool:
    """Checks whether a text string contains any Latin letters or numbers"""
    return self.p_contains_alphanum.match(chinese)

  def contains_notes(english: str) -> bool:
    """Guess whether an English equivalent contains notes"""
    return len(english) > 30 # Guess that test with more than 30 chars are notes


def compare_cc_cedict_cnotes(in_fname: str, out_fname: str):
  """Compares the cc_cedict and chinesenotes, reporting the differences

  Params:
    in_fname: Full path name of the cc-cedict file
    out_fname: Full path name of an output file
  """
  analyzer = EntryAnalyzer()
  cedict = open_cc_cedict(in_fname)
  if 'CNREADER_HOME' in os.environ:
    cn_home = os.environ['CNREADER_HOME']
    cnotes_fname = f'{cn_home}/data/words.txt'
  cnotes_dict = cndict.open_dictionary(cnotes_fname)
  absent_cnotes = 0
  absent_contain_alphanum = 0
  absent_single_char = 0
  absent_multiple_senses = 0
  absent_contains_notes = 0
  sample = 0
  with open(out_fname, 'w') as out_file:
    for trad, entry in cedict.items():
      if trad not in cnotes_dict:
        absent_cnotes += 1
        contains_alphanum = analyzer.contains_alphanum(trad)
        if contains_alphanum:
          absent_contain_alphanum += 1
        if len(trad) == 1:
          absent_single_char += 1
        if len(entry.senses) > 1:
          absent_multiple_senses += 1
        if EntryAnalyzer.contains_notes(entry.english):
          absent_contains_notes += 1
        if (sample < 100
            and not contains_alphanum
            and len(trad) > 1
            and not EntryAnalyzer.contains_notes(entry.english)
            and not len(entry.senses) > 1):
          _, _, pinyin = charutil.to_simplified(cnotes_dict, trad)
          out_file.write(
              f'{entry.simplified}\t{trad}\t{pinyin}\t{entry.english}\n')
          sample += 1
    print(f'absent_cnotes: {absent_cnotes}, absent_contain_alphanum: '
          f'{absent_contain_alphanum}, absent_single_char: {absent_single_char}, '
          f'absent_multiple_senses: {absent_multiple_senses}')

def open_cc_cedict(fname: str):
  """Reads the CC-CEDICT dictionary into memory

  Params:
    fname: the cedict_ts.u8 file is in the directory DICT_FILE_NAME below.
  Returns:
    A Python dictionary with traditional Chinese words as keys
  """
  cedict = {}
  pattern = re.compile(r'(.*) (.*) \[(.*)\] /(.*)/')
  with open(fname, 'r') as dict_file:
    line_num = 0
    for line in dict_file:
      line_num += 1
      line = line.strip()
      if not line:
        continue
      if line[0] == "#":
        continue
      match = pattern.search(line)
      if match:
        key = match.group(1)
        traditional = key
        simplified = match.group(2)
        pinyin = match.group(3)
        english = match.group(4)
        sense = WordSense(simplified, traditional, pinyin, english)
        entry = cedict.get(key, None)
        if not entry:
          entry = DictionaryEntry(simplified, [sense], f'{line_num}')
          cedict[key] = entry
        else:
          entry.add_word_sense(sense)
      else:
        logging.error(f'Could not parse line {line}\n')
  logging.info(f'open_cc_cedict completed with {len(cedict)} entries')
  return cedict


def main():
  """Command line entry point"""
  logging.basicConfig(level=logging.INFO)
  compare_cc_cedict_cnotes(DICT_FILE_NAME, 'out.tsv')


# Entry point from a script
if __name__ == '__main__':
  main()
