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
from typing import List, Mapping

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
    domain = EntryAnalyzer.guess_domain(entry)
    entry_analysis.domain = domain
    subdomain = EntryAnalyzer.guess_subdomain(entry)
    entry_analysis.subdomain = subdomain
    entity_kind = EntryAnalyzer.guess_entity_kind(entry)
    entry_analysis.entity_kind = entity_kind
    is_modern_named_entity = EntryAnalyzer.is_modern_named_entity(entry)
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

  def format_notes(self, trad):
    """Format notes with reference and moving from equivalent as needed"""
    english = self.entry.english
    notes = []
    if '(loanword)' in english:
      notes.append('Loanword')
    if '(Tw)' in english:
      notes.append('Taiwanese usage')
    notes_str = '; '.join(notes)
    ref = f'(CC-CEDICT \'{trad}\')'
    parts = [notes_str, ref]
    return ' '.join(parts)

  def reformat_english(self) -> str:
    """Reformats the English equivalent /"""
    english = self.entry.english
    if '/' in english:
      english = english.replace('/', ' / ')
    to_delete = ['(anatomy)', '(archaic term)', '(archeology)', '(astrology)',
                 '(botany)',
                 '(chemistry)',
                 '(computing)',
                 '(computer)', '(coll.)',
                 '(constellation)', '(drug)', '(dialect)', '(electronics)',
                 '(finance)',
                 '(geology)', '(geometry)', '(idiom)',
                 '(law)', '(language)', '(literary)', '(loanword)', '(math.)',
                 '(medicine)',
                 '(music)',
                 '(mythology)', '(onom.)', '(philosopher)', '(psychology)',
                 '(physics)',
                 '(slang)',
                 '(statistics)', '(Tw)']
    for term in to_delete:
      if term in english:
        english = english.replace(term, '')
        english = english.strip()
    return english

  def reformat_pinyin(self) -> str:
    """Reformats the pinyin string /"""
    simplified = self.entry.simplified
    tokens = cndict.tokenize_exclude_whole(self.wdict, simplified)
    pinyin = []
    for token in tokens:
      token_entry = self.wdict[token]
      pinyin.append(token_entry.senses[0].pinyin)
    if len(simplified) > 3:
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

  def check_keywords(keywords: List[str], target: str) -> bool:
    """Check for any of the keywords in a target string"""
    for keyword in keywords:
      if keyword in target:
        return True

  def contains_notes(english: str) -> bool:
    """Guess whether an English equivalent contains notes"""
    return len(english) > 30 # Guess that test with more than 30 chars are notes

  def guess_domain(entry: DictionaryEntry) -> str:
    """Guess the term domain, default modern Chinese"""
    english = entry.english
    chinese = entry.simplified
    comm_keywords = ['brand', 'company', 'website']
    if EntryAnalyzer.check_keywords(comm_keywords, english):
      return '商务\tCommerce'
    com_sci_keywords = ['algorithm', 'byte', 'computer', 'computing', 'code',
                        'network', 'server', 'software']
    if EntryAnalyzer.check_keywords(com_sci_keywords, english):
      return '计算机科学\tComputer Science'
    drama_keywords = ['film']
    if EntryAnalyzer.check_keywords(drama_keywords, english):
      return '戏剧\tDrama'
    if 'archaeological' in english or 'Khan' in english:
      return '历史\tHistory'
    if '(idiom)' in english:
      return '成语\tIdiom'
    place_keywords = ['capital', 'City', 'city', 'Lake', 'River', 'state',
                      'town', 'UK']
    place_keywords_zh = ['区', '镇']
    if (EntryAnalyzer.check_keywords(place_keywords, english) or
        EntryAnalyzer.check_keywords(place_keywords_zh, chinese)):
      return '地方\tPlaces'
    ling_keywords = ['linguistics', 'phonology']
    if EntryAnalyzer.check_keywords(ling_keywords, english):
      return '语言学\tLinguistics'
    lit_chin_keywords = ['archaic', '(literary)', '(old)']
    if EntryAnalyzer.check_keywords(lit_chin_keywords, english):
      return '文言文\tLiterary Chinese'
    if 'novelist' in english:
      return '文学\tLiterature'
    return '现代汉语\tModern Chinese'

  def guess_entity_kind(entry: DictionaryEntry) -> str:
    """Guess the entity kind, default empty"""
    english = entry.english
    chinese = entry.simplified
    animal_keywords_zh = ['狗', '蟹', '羊']
    if EntryAnalyzer.check_keywords(animal_keywords_zh, chinese):
      return '动物\tAnimal'
    if 'novelist' in english:
      return '作者\tAuthor'
    if 'constellation' in english:
       return '星座\tConstellation'
    if 'company' in english:
       return '星座\tConstellation'
    if 'county' in english or 'County' in english:
      return '县\tCounty'
    if 'city' in english or 'City' in english or 'capital' in english:
      return '城市\tCity'
    if 'Islands' in english:
      return '群岛\tIslands'
    if '鱼' in chinese or 'fish' in english:
      return '鱼\tFish'
    if '虫' in chinese:
      return '昆虫\tInsect'
    if 'Lake' in english:
      return '湖\tLake'
    if 'language' in english:
      return '语言\tLanguage'
    if '(drug)' in english:
      return '药品\tMedication'
    if '(mineral)' in english:
      return '矿物\tMineral'
    if 'nebula' in english:
      return '星云\tNebula'
    if 'River' in english:
      return '水名\tRiver'
    if 'Khan' in english or 'person name' in english or 'philosopher' in english:
      return '人\tPerson'
    if 'town' in english or 'UK' in english or 'prefecture' in english:
      return '地名\tPlace Name'
    if '镇' in chinese:
      return '地名\tPlace Name'
    if 'brand' in english:
      return '产品\tProduct'
    if 'state' in english:
      return '州\tState'
    if 'surname' in english:
      return '姓氏\tSurname'
    return '\\N\t\\N'

  def guess_grammar(chinese: str, english: str) -> str:
    """Guess what the part of speech is"""
    if english[0].isupper() or 'city' in english:
      return 'proper noun'
    if '(onom.)' in english:
      return 'onomatopoeia'
    if len(chinese) > 3:
      return 'set phrase'
    if len(english) > 1 and english[-2:] == 'ly':
      return 'adverb'
    if len(english) > 1 and english[-2:] == 'ed':
      return 'adjective'
    if len(english) > 2 and english[-3:] == 'ing':
      return 'adjective'
    if len(english) > 2 and english[-3:] == 'ive':
      return 'adjective'
    if len(english) > 3 and english[-4:] == 'ious':
      return 'adjective'
    if len(english) > 3 and english[-4:] == 'able':
      return 'adjective'
    if len(english) > 1 and english[:2] == 'to':
      return 'verb'
    return 'noun'

  def guess_subdomain(entry: DictionaryEntry) -> str:
    """Guess the term subdomain, default none, later check manually"""
    english = entry.english
    simplified = entry.simplified
    traditional = entry.traditional
    ag_keywords = ['agriculture', 'farming']
    if EntryAnalyzer.check_keywords(ag_keywords, english):
      return '农业\tAgriculture'
    arch_keywords = ['archeology']
    if EntryAnalyzer.check_keywords(arch_keywords, english):
      return '考古学 Archaeology'
    arts_keywords = ['fine arts']
    if EntryAnalyzer.check_keywords(arts_keywords, english):
      return '艺术\tArt'
    astrol_keywords = ['astrology', 'divination']
    if EntryAnalyzer.check_keywords(astrol_keywords, english):
      return '占星术\tAstrology'
    astr_keywords = ['astronomy', 'constellation', 'nebula', 'galaxy', '(star)']
    astr_keywords_zh = ['星']
    if (EntryAnalyzer.check_keywords(astr_keywords, english) or
        EntryAnalyzer.check_keywords(astr_keywords_zh, simplified)):
      return '天文\tAstronomy'
    bio_keywords = ['bacteria', 'biology', '(cell)', 'organism']
    bio_keywords_zh = ['脂肪']
    if (EntryAnalyzer.check_keywords(bio_keywords, english) or
         EntryAnalyzer.check_keywords(bio_keywords_zh, simplified)):
      return '生物学\tBiology'
    bot_keywords = ['botany']
    if EntryAnalyzer.check_keywords(bot_keywords, english):
      return '植物学\tBotany'
    chin_med_keywords = ['acupuncture', 'TCM']
    if EntryAnalyzer.check_keywords(chin_med_keywords, english):
     return '中医\tChinese Medicine'
    chem_keywords = ['acid', 'C2', 'C3', 'C4', 'C5', 'alcohol', 'biochemistry',
                     'chemical', 'chemistry', 'chloride', 'fluoride', 'hydrate',
                     'lactose', 'molecular','oxide', 'sulfur']
    if EntryAnalyzer.check_keywords(chem_keywords, english):
      return '化学\tChemistry'
    chem_keywords_zh = ['毒素']
    if EntryAnalyzer.check_keywords(chem_keywords_zh, simplified):
      return '化学\tChemistry'
    china_keywords = ['Sichuan', 'Anhui', 'Hainan', 'Hebei', 'Inner Mongolia',
                      'Hong Kong', 'Xinjiang']
    if EntryAnalyzer.check_keywords(china_keywords, english):
      return '中国\tChina'
    chr_keywords = ['Bible', 'biblical', 'Christian', 'Testament']
    if EntryAnalyzer.check_keywords(chr_keywords, english):
      return '基督教\tChristianity'
    cloth_keywords_zh = ['裤', '衫', '鞋']
    if EntryAnalyzer.check_keywords(cloth_keywords_zh, simplified):
      return '服装\tClothing'
    dance_keywords = ['dance']
    if EntryAnalyzer.check_keywords(dance_keywords, english):
      return '跳舞\tDancing'
    dialect_keywords = ['Cantonese', 'dialect', 'erhua variant']
    if EntryAnalyzer.check_keywords(dialect_keywords, english):
      return '方言\tDialect'
    econ__keywords = ['economics']
    if EntryAnalyzer.check_keywords(econ__keywords, english):
      return '经济\tEconomics'
    elec_keywords = ['circuit', '(electronics)', '(elec.)', 'semiconductor']
    if EntryAnalyzer.check_keywords(elec_keywords, english):
      return '电子工程\tElectronic Engineering'
    eng_keywords = ['UK']
    if EntryAnalyzer.check_keywords(eng_keywords, english):
      return '英国\tEngland'
    eu_keywords = ['Germany', 'Holland']
    if EntryAnalyzer.check_keywords(eu_keywords, english):
      return '欧洲\tEurope'
    fin_keywords = ['accountancy', 'accounting', 'finance']
    if EntryAnalyzer.check_keywords(fin_keywords, english):
      return '财会\tFinance and Accounting'
    food_keywords = ['drink', 'food']
    food_keywords_zh = ['饼', '菜', '餐', '茶', '果',  '酱', '酒', '咖啡', '米',
                        '肉', '烧']
    food_keywords_zh_tw = ['麵']
    if (EntryAnalyzer.check_keywords(food_keywords, english) or
        EntryAnalyzer.check_keywords(food_keywords_zh, simplified) or
        EntryAnalyzer.check_keywords(food_keywords_zh_tw, traditional)):
      return '饮食\tFood and Drink'
    geog_keywords = ['geography', 'Islands', 'Ocean', 'ocean', 'peninsula']
    if EntryAnalyzer.check_keywords(geog_keywords, english):
      return '地理\tGeography'
    geo_keywords = ['geology', 'mineral', 'rock']
    if EntryAnalyzer.check_keywords(geo_keywords, english):
      return '地质\tGeology'
    geom_keywords = ['geometry']
    if EntryAnalyzer.check_keywords(geom_keywords, english):
      return '几何\tGeometry'
    gram_keywords = ['grammar']
    gram_keywords_zh = ['句']
    if (EntryAnalyzer.check_keywords(gram_keywords, english) or
        EntryAnalyzer.check_keywords(gram_keywords_zh, simplified)):
      return '语法\tGrammar'
    law_keywords = ['criminal', 'judicial', '(law)']
    if EntryAnalyzer.check_keywords(law_keywords, english):
      return '法律\tLaw'
    math_keywords = ['algebra', 'equation', 'math']
    math_keywords_zh = ['函数']
    if (EntryAnalyzer.check_keywords(math_keywords, english) or
        EntryAnalyzer.check_keywords(math_keywords_zh, simplified)):
      return '数学\tMathematics'
    med_keywords = ['anatomy', 'coronary', 'disease', 'disorder',
                    '(drug)', 'erosis', 'fever', 'itis', 'medical', 'medicine',
                    '(med.)',
                    'paralysis', 'physiology', 'syndrome', 'therapy', 'vaccine',
                    'virus']
    med_keywords_zh = ['病', '激素', '症']
    if (EntryAnalyzer.check_keywords(med_keywords, english) or
        EntryAnalyzer.check_keywords(med_keywords_zh, simplified)):
      return '医学\tMedicine'
    mil_keywords = ['bomb' , 'military', 'missile', 'warfare', 'weapon']
    if EntryAnalyzer.check_keywords(mil_keywords, english):
      return '军事\tMilitary'
    music_keywords = ['guitar', 'music', '(opera)']
    music_keywords_zh = ['歌', '琴', '曲']
    if (EntryAnalyzer.check_keywords(music_keywords, english) or 
        EntryAnalyzer.check_keywords(music_keywords_zh, simplified)):
       return '音乐\tMusic'
    myth_keywords = ['deity', 'mythology']
    if EntryAnalyzer.check_keywords(myth_keywords, english):
      return '神话\tMythology'
    names_keywords = ['(name)']
    if EntryAnalyzer.check_keywords(names_keywords, english):
      return '名字\tNames'
    optics_keywords = ['optical', 'optics']
    if EntryAnalyzer.check_keywords(names_keywords, english):
      return '光学\tOptics'
    pal_keywords = ['dinosaur', 'fossil', 'paleo']
    if EntryAnalyzer.check_keywords(pal_keywords, english):
      return '古生物学\tPaleontology'
    phil_keywords = ['philosopher', 'philosophy']
    if EntryAnalyzer.check_keywords(phil_keywords, english):
      return '哲学\tPhilosophy'
    pol_keywords = ['political']
    if EntryAnalyzer.check_keywords(pol_keywords, english):
      return '政治\tPolitics'
    pysc_keywords = ['(psych.)', 'psychology']
    if EntryAnalyzer.check_keywords(pysc_keywords, english):
      return '心理学\tPsychology'
    phys_keywords = ['(mechanics)', 'physics']
    if EntryAnalyzer.check_keywords(phys_keywords, english):
      return '物理\tPhysics'
    rel_keywords = ['religion']
    if EntryAnalyzer.check_keywords(rel_keywords, english):
      return '宗教\tReligion'
    spok_keywords = ['(coll.)']
    if EntryAnalyzer.check_keywords(spok_keywords, english):
      return '口语\tSpoken Language'
    slang_keywords = ['curse', 'netspeak', 'slang']
    if EntryAnalyzer.check_keywords(slang_keywords, english):
      return '俚语\tSlang'
    sport_keywords = ['ball', 'gymnastics', 'soccer', 'sport']
    if EntryAnalyzer.check_keywords(sport_keywords, english):
      return '体育\tSport'
    stats_keywords = ['statistics']
    if EntryAnalyzer.check_keywords(stats_keywords, english):
      return '统计学\tStatistics'
    us_keywords = ['state', 'Pennsylvania']
    if EntryAnalyzer.check_keywords(stats_keywords, english):
      return '美国\tUnited States'
    zoo_keywords = ['fish', 'zoology']
    zoo_keywords_zh = ['猫', '虫', '狗', '蟹', '羊', '鱼']
    if (EntryAnalyzer.check_keywords(zoo_keywords, english) or
        EntryAnalyzer.check_keywords(zoo_keywords_zh, simplified)):
      return '动物学\tZoology'
    return '\\N\t\\N'

  def is_modern_named_entity(entry: DictionaryEntry) -> bool:
    """Guess whether the term is a modern named entity"""
    chinese = entry.simplified
    english = entry.english
    entity_keywords = ['Afghan', 'Airlines', 'brand', 'Canadian', 'Canada',
                       'Colorado', 'company', 'comic', 'Cuba',
                       'France', 'French', 'Germany', 'Harry Potter', 'Holland',
                       'Idaho',
                       'Indonesian',
                       'Italy', 'Ireland', 'Japan', 'Journal',
                       'male name',
                       '(name)', 'Korea', 'London', 'Manhattan', 'manufacturer',
                       'Netherlands', 'Nevada',
                       'Norway',
                       'person name',
                       'proper name',
                       'Pakistan', 'Pennsylvania', 'Russia', 'Spain', 'state',
                       'surname',
                       'Sudan',  'Sweden', 'Tokyo', '(U.S.)', 'University',
                       'video game',
                       'website', 'Zimbabwe']
    entity_keywords_zh = ['·', '，']
    if (EntryAnalyzer.check_keywords(entity_keywords, english) or
        EntryAnalyzer.check_keywords(entity_keywords_zh, chinese)):
      return True
    if len(chinese) > 3 and len(english) > 1 and english[0].isupper():
      return True
    return False


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
  luid = 120612
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
          english = formatter.reformat_english()
          pinyin = formatter.reformat_pinyin()
          notes = formatter.format_notes(trad)
          out_file.write(f'{luid}\t{entry.simplified}\t{traditional}\t'
              f'{pinyin}\t{english}\t{grammar}\t{entity_kind}\t{domain}\t'
              f'{subdomain}\t{empty}\t{notes}\t{luid}\n')
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
