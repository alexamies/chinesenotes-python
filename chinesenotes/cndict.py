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

from chinesenotes.cndict_types import DictionaryEntry
from chinesenotes.cndict_types import WordSense

PINYIN_CONVERSION = {'ā': ('a', 1), 'á': ('a', 2), 'ǎ': ('a', 3), 'à': ('a', 4),
                     'ē': ('e', 1), 'é': ('e', 2), 'ě': ('e', 3), 'è': ('e', 4),
                     'ī': ('i', 1), 'í': ('i', 2), 'ǐ': ('i', 3), 'ì': ('i', 4),
                     'ō': ('o', 1), 'ó': ('o', 2), 'ǒ': ('o', 3), 'ò': ('o', 4),
                     'ū': ('u', 1), 'ú': ('u', 2), 'ǔ': ('u', 3), 'ù': ('u', 4)}


def convert_to_cccedict(infile: str, outfile: str):
  """Converts the Chinese Notes dictionary from native format to CC-CEDICT

  Since there are utilities available that use the CC-CEDICT format, it can be
  useful to have the dicitonary in that format.
  """
  wdict = open_dictionary(infile)
  with open(outfile, 'w') as outf:
    done = set()
    for key in wdict:
      entry = wdict[key]
      simplified = entry.simplified
      traditional = entry.traditional
      if traditional == '\\N':
        traditional = simplified
      if simplified in done or traditional in done:
        continue
      pinyin = entry.pinyin
      pinyin = _convert_pinyin_numeric(simplified, wdict)
      english = entry.english
      if english == '\\N':
        continue
      outf.write(f'{traditional} {simplified} [{pinyin}] /{english}/\n')
      done.add(simplified)
      done.add(traditional)


def lookup(wdict: Mapping[str, DictionaryEntry],
           keyword: str) -> DictionaryEntry:
  """Looks up the keyword in the dictionary or return None if it is not there
  """
  return wdict[keyword]


def open_dictionary(fname: str,
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
  if fname.startswith('https'):
    wdict = _load_from_url(fname, chinese_only)
  else:
    wdict = _load_locally(fname, chinese_only)
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
  logging.info('Opening dictionary from local file ')
  with open(fname, 'r') as dict_file:
    return _load_dictionary(dict_file, chinese_only)

def _convert_pinyin_numeric(simplified: str,
                            wdict: Mapping[str, DictionaryEntry]) -> str:
  """Convert pinyin from a format like ā to a1 with spaces between the syllables

  For example, fēnsàn -> fen1 san4
  """
  new_pinyin = []
  for character in simplified:
    if character not in wdict:
      continue
    term = wdict[character]
    pinyini = term.pinyin
    new_char_pinyin = []
    tone_number = ''
    for letter in pinyini:
      tone_number = ''
      if letter in PINYIN_CONVERSION:
        regular_letter = PINYIN_CONVERSION[letter][0]
        tone_number = str(PINYIN_CONVERSION[letter][1])
        new_char_pinyin.append(regular_letter)
      else:
        new_char_pinyin.append(letter)
    new_char_pinyin.append(tone_number)
    new_pinyin.append(''.join(new_char_pinyin))
  return ' '.join(new_pinyin)


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
  parser.add_argument('--convert',
                      dest='convert',
                      help='Convert to CC-CEDICT format with given output file')
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
  elif args.convert:
    logging.info('Converting to CC-CEDICT format with output file '
                 '{args.convert}')
    convert_to_cccedict(fname, args.convert)
    print('Done')

# Entry point from a script
if __name__ == '__main__':
  main()
