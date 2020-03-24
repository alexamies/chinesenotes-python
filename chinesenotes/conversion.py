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

See the CC-CEDICT Wiki at https://cc-cedict.org/wiki/start
Download the CC-CEDICT file from
https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip
"""

import argparse
import logging
import os
import re
from typing import Mapping

from chinesenotes import charutil
from chinesenotes import cndict
from chinesenotes.cndict_types import DictionaryEntry
from chinesenotes.cndict_types import WordSense


PINYIN_CONVERSION = {'ā': ('a', 1), 'á': ('a', 2), 'ǎ': ('a', 3), 'à': ('a', 4),
                     'ē': ('e', 1), 'é': ('e', 2), 'ě': ('e', 3), 'è': ('e', 4),
                     'ī': ('i', 1), 'í': ('i', 2), 'ǐ': ('i', 3), 'ì': ('i', 4),
                     'ō': ('o', 1), 'ó': ('o', 2), 'ǒ': ('o', 3), 'ò': ('o', 4),
                     'ū': ('u', 1), 'ú': ('u', 2), 'ǔ': ('u', 3), 'ù': ('u', 4)}


class EntryAnalysis:
  """Contains results of entry analysis"""

  def __init__(self,
               contains_alphanum: bool,
               refers_to_variant: bool,
               grammar: str,
               contains_notes: bool):
    self.contains_alphanum = contains_alphanum
    self.refers_to_variant= refers_to_variant
    self.grammar = grammar
    self.contains_notes = contains_notes
    self.domain = None
    self.entity_kind = None
    self.subdomain = None
    self.is_modern_named_entity = False


class ComparisonSummary:
  """Summary of the comparison between dictionaries"""

  def __init__(self, name1: str, name2: str):
    """Constructor"""
    self.name1 = name1
    self.name2 = name2
    self.analyzer = EntryAnalyzer()
    self.absent_dict2 = 0
    self.absent_contain_alphanum = 0
    self.absent_single_char = 0
    self.absent_multiple_senses = 0
    self.absent_contains_notes = 0
    self.absent_refers_to_variant = 0
    self.modern_named_entities = 0
    self.p_contains_alphanum = re.compile('.*[a-zA-Z0-9]+')
    self.p_refers_to_variant= re.compile('(variant|see)')

  def increment_absent_dict2(self, entry: DictionaryEntry) -> EntryAnalysis:
    self.absent_dict2 += 1
    simplified = entry.simplified
    contains_alphanum = self.analyzer.contains_alphanum(simplified)
    refers_to_variant = self.analyzer.refers_to_variant(entry.english)
    grammar = EntryAnalyzer.guess_grammar(entry.simplified, entry.english)
    contains_notes = EntryAnalyzer.contains_notes(entry.english)
    entry_analysis = EntryAnalysis(contains_alphanum,
                                   refers_to_variant,
                                   grammar,
                                   contains_notes)
    domain = EntryAnalyzer.guess_domain(entry.english)
    entry_analysis.domain = domain
    subdomain = EntryAnalyzer.guess_subdomain(entry.english)
    entry_analysis.subdomain = subdomain
    entity_kind = EntryAnalyzer.guess_entity_kind(entry.english)
    entry_analysis.entity_kind = entity_kind
    is_modern_named_entity = EntryAnalyzer.is_modern_named_entity(simplified)
    entry_analysis.is_modern_named_entity = is_modern_named_entity
    if contains_alphanum:
      self.absent_contain_alphanum += 1
    if len(simplified) == 1:
      self.absent_single_char += 1
    if len(entry.senses) > 1:
      self.absent_multiple_senses += 1
    if contains_notes:
      self.absent_contains_notes += 1
    if refers_to_variant:
      self.absent_refers_to_variant += 1
    if is_modern_named_entity:
      self.modern_named_entities += 1
    return entry_analysis

  def print_summary(self):
    print(f'Present in {self.name1}, absent in {self.name2}, '
        f'num absent: {self.absent_dict2}\n'
        f'containing alphanum: {self.absent_contain_alphanum}\n'
        f'single char: {self.absent_single_char}\n'
        f'multiple senses: {self.absent_multiple_senses}\n'
        f'refers_to_variant: {self.absent_refers_to_variant}\n'
        f'modern_named_entities: {self.modern_named_entities}')


class EntryFormatter:
  """Methods for formatting entries"""

  def __init__(self,
               wdict: Mapping[str, DictionaryEntry],
               entry: DictionaryEntry):
    """Constructor"""
    self.entry = entry
    self.wdict = wdict

  def add_space_slash(self) -> str:
    """Adds space around a forward slash /"""
    english = self.entry.english
    if '/' in english:
      return english.replace('/', ' / ')
    return english

  def reformat_pinyin(self) -> str:
    """Reformats the pinyin string /"""
    simplified = self.entry.simplified
    tokens = cndict.tokenize_exclude_whole(self.wdict, simplified)
    pinyin = []
    for token in tokens:
      token_entry = self.wdict[token]
      pinyin.append(token_entry.senses[0].pinyin)
    if len(simplified) > 4:
      return ' '.join(pinyin)
    return ''.join(pinyin)


class EntryAnalyzer:
  """Methods for analyzing entries"""

  def __init__(self):
    self.p_contains_alphanum = re.compile('.*[a-zA-Z0-9]+')
    self.p_refers_to_variant= re.compile('(variant|see)')


  def contains_alphanum(self, chinese: str) -> bool:
    """Checks whether a text string contains any Latin letters or numbers"""
    return self.p_contains_alphanum.match(chinese)

  def refers_to_variant(self, english: str) -> bool:
    """Guess whether the entry is a reference to a variant"""
    return self.p_refers_to_variant.match(english)

  def contains_notes(english: str) -> bool:
    """Guess whether an English equivalent contains notes"""
    return len(english) > 30 # Guess that test with more than 30 chars are notes

  def guess_domain(english: str) -> str:
    """Guess the term domain, default modern Chinese"""
    if '(idiom)' in english:
      return '成语\tIdiom'
    if ('(computing)' in english or
       'code' in english or
       'network' in english or
       'server' in english):
      return '计算机科学\tComputer Science'
    if ('City' in english or
        'city' in english or
        'county' in english or
        'Lake' in english or
        'River' in english or
        'state' in english):
      return '地方\tPlaces'
    if 'film' in english:
      return '戏剧\tDrama'
    if 'linguistics' in english:
      return '语言学\tLinguistics'
    return '现代汉语\tModern Chinese'

  def guess_entity_kind(english: str) -> str:
    """Guess the entity kind, default empty"""
    if 'county' in english:
      return '县\tCounty'
    if 'city' in english or 'City' in english:
      return '城市\tCity'
    if 'Lake' in english:
      return '湖\tLake'
    if '(language)' in english:
      return '语言\tLanguage'
    if 'state' in english:
      return '州\tState'
    return '\\N\t\\N'

  def guess_grammar(chinese: str, english: str) -> str:
    """Guess what the part of speech is"""
    pos = 'noun'
    if english[0].isupper() or 'city' in english:
      pos = 'proper noun'
    elif len(chinese) > 3:
      pos = 'set phrase'
    elif len(english) > 1 and english[-2:] == 'ed':
      pos = 'adjective'
    elif len(english) > 1 and english[:2] == 'to':
      pos = 'verb'
    return pos

  def guess_subdomain(english: str) -> str:
    """Guess the term subdomain, default none, later check manually"""
    if 'nebula' in english or 'constellation' in english or 'galaxy' in english:
      return '天文\tAstronomy'
    if 'biology' in english:
      return '生物学\tBiology'
    if ('(chemistry)' in english
        or 'acid' in english
        or 'tyl' in english
        or 'alcohol' in english
        or 'oxide' in english):
      return '化学\tChemistry'
    if 'Christianity' in english or 'Testament' in english:
      return '基督教\tChristianity'
    if '(dialect)' in english:
      return '方言\tDialect'
    if 'fruit' in english:
      return '饮食\tFood and Drink'
    if 'geometry' in english:
      return '几何\tGeometry'
    if '(law)' in english:
      return '法律\tLaw'
    if 'math' in english or 'algebra' in english:
      return '数学\tMathematics'
    if 'military' in english:
      return '军事\tMilitary'
    if ('itis' in english
        or 'anatomy' in english
        or 'disease' in english
        or 'physiology' in english
        or 'syndrome' in english
        or 'virus' in english
        or 'medical' in english):
      return '医学\tMedicine'
    if '(name)' in english:
      return '名字\tNames'
    if 'physics' in english or 'electric' in english:
      return '物理\tPhysics'
    if '(coll.)' in english:
      return '口语\tSpoken Language'
    if 'ball' in english or 'soccer' in english:
      return '体育\tSport'
    if 'curse' in english:
      return '俚语\tSlang'
    if 'state' in english:
      return '美国\tUnited States'
    return '\\N\t\\N'

  def is_modern_named_entity(chinese: str) -> bool:
    """Guess whether the term is a modern named entity"""
    return '·' in chinese


def compare_cc_cedict_cnotes(in_fname: str, out_fname: str):
  """Compares the cc_cedict and chinesenotes, reporting the differences

  Writes the output to out_fname and prints a summary to the console
  Params:
    in_fname: Full path name of the cc-cedict file
    out_fname: Full path name of an output file
  """
  summary = ComparisonSummary('CC-CEDICT', 'Chinese Notes')
  analyzer = EntryAnalyzer()
  cedict = open_cc_cedict(in_fname)
  cnotes_dict = cndict.open_dictionary()
  sample = 0
  luid = 117348
  with open(out_fname, 'w') as out_file:
    for trad, entry in cedict.items():
      if trad not in cnotes_dict:
        entry_analysis = summary.increment_absent_dict2(entry)
        if (sample < 100
            and not entry_analysis.contains_alphanum
            and len(trad) > 1
            and not entry_analysis.contains_notes
            and not len(entry.senses) > 1
            and not entry_analysis.refers_to_variant
            and not entry_analysis.is_modern_named_entity):
          grammar = entry_analysis.grammar
          traditional = trad
          if entry.simplified == trad:
            traditional = '\\N'
          empty = '\\N\t\\N'
          entity_kind = entry_analysis.entity_kind
          domain = entry_analysis.domain
          subdomain = entry_analysis.subdomain
          formatter = EntryFormatter(cnotes_dict, entry)
          english = formatter.add_space_slash()
          pinyin = formatter.reformat_pinyin()
          out_file.write(f'{luid}\t{entry.simplified}\t{traditional}\t'
              f'{pinyin}\t{english}\t{grammar}\t{entity_kind}\t{domain}\t'
              f'{subdomain}\t{empty}\t(CC-CEDICT \'{trad}\')\t{luid}\n')
          sample += 1
          luid += 1
    summary.print_summary()


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


def to_cc_cedict(infile: str, outfile: str):
  """Converts the Chinese Notes dictionary from native format to CC-CEDICT

  Since there are utilities available that use the CC-CEDICT format, it can be
  useful to have the dicitonary in that format.
  """
  wdict = cndict.open_dictionary(infile)
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
  parser = argparse.ArgumentParser()
  parser.add_argument('--to_cnotes',
                      dest='to_cnotes',
                      help='Convert to Chinese Notes format with given output '
                      'file')
  parser.add_argument('--to_cc_cedict',
                      dest='to_cc_cedict',
                      help='Convert to CC-CEDICT format with given output file')
  args = parser.parse_args()
  if args.to_cnotes:
    compare_cc_cedict_cnotes(args.to_cnotes, 'out.tsv')
  elif args.to_cc_cedict:
    logging.info('Converting to CC-CEDICT format with output file '
                 '{args.convert}')
    to_cc_cedict(fname, args.to_cc_cedict)
    print('Done')



# Entry point from a script
if __name__ == '__main__':
  main()
