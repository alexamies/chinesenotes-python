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
    self.ignore = False
    self.contains_punctuation = False


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
    self.ignore = 0
    self.contains_punctuation = 0
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
    domain = self.analyzer.guess_domain(entry)
    entry_analysis.domain = domain
    subdomain = EntryAnalyzer.guess_subdomain(entry)
    entry_analysis.subdomain = subdomain
    entity_kind = EntryAnalyzer.guess_entity_kind(entry)
    entry_analysis.entity_kind = entity_kind
    is_modern_named_entity = self.analyzer.is_modern_named_entity(entry)
    entry_analysis.is_modern_named_entity = is_modern_named_entity
    ignore = EntryAnalyzer.ignore(entry)
    entry_analysis.ignore = ignore
    contains_punctuation = EntryAnalyzer.contains_punctuation(entry.simplified)
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
    if ignore:
      self.ignore += 1
    if contains_punctuation:
      self.contains_punctuation += 1
    return entry_analysis

  def print_summary(self):
    print(f'Present in {self.name1}, absent in {self.name2}, '
        f'num absent: {self.absent_dict2}\n'
        f'containing alphanum: {self.absent_contain_alphanum}\n'
        f'single char: {self.absent_single_char}\n'
        f'multiple senses: {self.absent_multiple_senses}\n'
        f'refers_to_variant: {self.absent_refers_to_variant}\n'
        f'modern_named_entities: {self.modern_named_entities}\n'
        f'contains_notes: {self.absent_contains_notes}\n'
        f'ignore: {self.ignore}\n'
         f'contains_punctuation: {self.contains_punctuation}\n'
        )


class EntryFormatter:
  """Methods for formatting entries"""

  def __init__(self,
               wdict: Mapping[str, DictionaryEntry],
               entry: DictionaryEntry):
    """Constructor"""
    self.entry = entry
    self.wdict = wdict
    self._idiom_re = re.compile(r'.*\(idiom, (.*)\)', re.IGNORECASE)
    self._loanword_re = re.compile(r'.*\((loanword.*)\)', re.IGNORECASE)
    self._notes_re = re.compile(r'.*(county in.+'
                                r'|county of.+'
                                r'|county level city.+'
                                r'|prefecture level city.+'
                                r'|prefecture-level city.+'
                                r'|district of.+'
                                r'|district in.+'
                                r'|Lake in.+'
                                r'|town in.+'
                                r'|township in.+'
                                ')$',
                                re.IGNORECASE)
    self._pinyin_re = re.compile(r'.*(\[.*\]).*')
    self._pipe_re = re.compile(r'.* (.+\|).*')
    self._abbreviation_re = re.compile(r'.*(/.?abbr. '
                                       r'|\(abbr. '
                                       r'|, abbr. )(.+)$')
    self._classifier_re = re.compile(r'.*(/ CL:.+)$')
    self._also_re = re.compile(r'.*(/.?also written|/.?see also|/.?same as)(.+)$')
    self._unit_re = re.compile(r'.*\((Chinese unit .+)\)')
    self._also_pron_re = re.compile(r'.*(/ also pr.+)$')
    self._year_re = re.compile(r'(.*)\((.*[0-9][0-9][0-9][0-9].*)\)(.*)')

  def format_notes(self, trad):
    """Format notes with reference and moving from equivalent as needed"""
    english = self.entry.english
    notes = []
    m = self._notes_re.match(english)
    if m:
      note = m.group(1)
      note = note[0].upper() + note[1:]
      notes.append(note)
    m_idiom = self._idiom_re.match(english)
    if m_idiom:
      note = m_idiom.group(1)
      note = note[0].upper() + note[1:]
      note = note.replace('"', '')
      notes.append(note)
    m_loanword = self._loanword_re.match(english)
    if m_loanword:
      note = m_loanword.group(1)
      note = note[0].upper() + note[1:]
      notes.append(note)
    m_abbrev = self._abbreviation_re.match(english)
    if m_abbrev:
      note = 'Abbreviation ' + m_abbrev.group(2)
      notes.append(note)
    m_also = self._also_re.match(english)
    if m_also:
      note = m_also.group(1) + m_also.group(2)
      note = note[1:].strip()
      note = note[0].upper() + note[1:]
      notes.append(note)
    m_unit = self._unit_re.match(english)
    if m_unit:
      note = m_unit.group(1)
      notes.append(note)
    if '(loanword)' in english:
      notes.append('Loanword')
    if '(Tw)' in english:
      notes.append('Taiwanese usage')
    if '(Cantonese)' in english:
      notes.append('Cantonese')
    if '(Internet slang)' in english:
      notes.append('Internet slang')
    if '(derog.)' in english:
      notes.append('Derogatory')
    if '(bird species of China)' in english:
      notes.append('Bird species of China')
    m_year = self._year_re.match(english)
    if m_year:
      explanation = m_year.group(3)
      if explanation:
        if explanation[0] == ',':
          explanation = explanation[1:]
          explanation = explanation.strip()
        explanation = explanation[0].upper() + explanation[1:]
        note = m_year.group(2) + '; ' + explanation
      else:
        note = m_year.group(2)
      notes.append(note)
    parts = []
    if notes:
      notes_str = '; '.join(notes)
      parts.append(notes_str)
    ref = f'(CC-CEDICT \'{trad}\')'
    parts.append(ref)
    notes = ' '.join(parts)
    # Delete pinyin in notes
    m_pinyin = self._pinyin_re.match(notes)
    if m_pinyin:
      pinyin_br = m_pinyin.group(1)
      notes = notes.replace(pinyin_br, '')
    # Replace trad|simplified in notes with simplified only
    m_pipe = self._pipe_re.match(notes)
    if m_pipe:
      trad_alt = m_pipe.group(1)
      notes = notes.replace(trad_alt, '')
    return notes

  def reformat_english(self) -> str:
    """Reformats the English equivalent /"""
    english = self.entry.english
    if '; ' in english:
      english = english.replace(';', '/')
    m = self._notes_re.match(english)
    if m:
      english = english.replace(m.group(1), '')
    m_idiom = self._idiom_re.match(english)
    if m_idiom:
      note = '(idiom, ' + m_idiom.group(1) + ')'
      english = english.replace(note, '')
    m_loanword = self._loanword_re.match(english)
    if m_loanword:
      note = '(' + m_loanword.group(1) + ')'
      english = english.replace(note, '')
    m_abbrev = self._abbreviation_re.match(english)
    if m_abbrev:
      note = m_abbrev.group(1) + m_abbrev.group(2)
      english = english.replace(note, '')
    m_classifier = self._classifier_re.match(english)
    if m_classifier:
      note = m_classifier.group(1)
      english = english.replace(note, '')
    m_also = self._also_re.match(english)
    if m_also:
      note = m_also.group(1) + m_also.group(2)
      english = english.replace(note, '')
    m_unit = self._unit_re.match(english)
    if m_unit:
      note = '(' + m_unit.group(1) + ')'
      english = english.replace(note, '')
    m_also_pron = self._also_pron_re.match(english)
    if m_also_pron:
      english = english.replace(m_also_pron.group(1), '')
    m_year = self._year_re.match(english)
    if m_year:
      english = m_year.group(1)
    to_delete = ['"', '(accountancy)', '(accounting)', '(agriculture)',
                 '(anatomy)',
                 '(archaic term)', '(arch.)', '(archaic)', '(archeology)',
                 '(archaeology)', '(art)', '(astrology)', '(astron.)',
                 '(astronomy)', '(athletics)', '(biochemistry)',
                 '(biology)', '(bird species of China)', '(botany)',
                 '(Buddhism)',
                 '(Cantonese)', '(chemistry)', '(Chinese medicine)',
                 '(Christian ceremony)', '(classical)', '(computing)',
                 '(computer)', '(coll.)', '(colloquial)', 
                 '(constellation)', '(drug)', '(dialect)', '(dialectal)',
                 '(dance)', '(derog.)',
                 '(economics)',
                 '(elec.)', '(electrical engineering)', '(electronics)',
                 'ethnic minority', '(fig.)', 'fig.',
                 '(finance)',
                 '(geography)', '(geology)', '(geometry)', '(grammar)',
                 '(history)', '(idiom)', 'in Xinjiang',
                 '(interjection)', '(Internet slang)', ', Jilin',
                 '(law)', '(language)', '(linguistics)', '(lit.)', 'lit.',
                 '(literary)',
                 '(loanword)', '- Martial Art', '(math.)', '(math)',
                 '(medical term)', '(medicine)', '(military)',
                 '(molecular biology)', '(music)',
                 '(mythology)', 'of Beijing', 'of Hong Kong', '(old)',
                 '(old usage)',
                 '(onom.)',
                 '(philosopher)', '(philosophy)', '(photography)', '(proverb)',
                 '(psychology)',
                 '(physics)', ', Shanghai',
                 '(slang)', '(sport)', '(sports)',
                 '(statistics)', '/ Taiwan pr.', ',  Tibet', '(Tw)',
                 '(zoology)']
    for term in to_delete:
      if term in english:
        english = english.replace(term, '')
        english = english.strip()
    m2 = self._pinyin_re.match(english)
    if m2:
      pinyin_br = m2.group(1)
      english = english.replace(pinyin_br, '')
    if '/' in english:
      parts = english.split('/')
      sparts = []
      for part in parts:
        sparts.append(part.strip())
      english = ' / '.join(sparts)
    english = english.strip()
    if len(english) > 100:
      english = EntryFormatter.shorten_english(english)
    return english

  def reformat_pinyin(self) -> str:
    """Reformats the pinyin string /"""
    simplified = self.entry.simplified
    tokens = cndict.tokenize_exclude_whole(self.wdict, simplified)
    pinyin = []
    for token in tokens:
      if token == '·':
        #pinyin.append(' ')
        pass
      elif token == '，':
        pinyin.append(', ')
      else:
        try:
          token_entry = self.wdict[token]
          pinyin.append(token_entry.senses[0].pinyin)
        except KeyError as ex:
          print(f'reformat_pinyin KeyError {self.entry.traditional}')
          raise
    if len(simplified) > 3:
      pinyin = ' '.join(pinyin)
      pinyin = pinyin.replace(" , ", ", ")
      pinyin = pinyin.replace(",  ", ", ")
      return pinyin
    return ''.join(pinyin)

  def shorten_english(english) -> str:
    """Shortens the English equivalent string """
    parts = english.split(' / ')
    if len(parts) > 1:
      english =' / '.join(parts[:len(parts)-1])
    return english


class EntryAnalyzer:
  """Methods for analyzing entries"""

  def __init__(self):
    self.p_contains_alphanum = re.compile('.*[a-zA-Z0-9]+')
    self.p_contains_16xx = re.compile('.*16[0-9][0-9].*')
    self.p_contains_17xx = re.compile('.*17[0-9][0-9].*')
    self.p_contains_18xx = re.compile('.*18[0-9][0-9].*')
    self.p_contains_19xx = re.compile('.*19[1-9][0-9].*')
    self.p_contains_2xxx = re.compile('.*2[0-2][0-9][0-9].*')
    self.p_refers_to_variant= re.compile('(variant|see)')


  def contains_alphanum(self, chinese: str) -> bool:
    """Checks whether a text string contains any Latin letters or numbers"""
    return self.p_contains_alphanum.match(chinese)

  def contains_punctuation(chinese: str) -> bool:
    """Checks whether a text string contains any Chinese punctuation"""
    if '、' in chinese or '，' in chinese:
      # print(f'Contains punc: {chinese}')
      return True

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
    return len(english) > 70 # Guess that test with more chars are notes

  def guess_domain(self, entry: DictionaryEntry) -> str:
    """Guess the term domain, default modern Chinese"""
    english = entry.english
    chinese = entry.simplified
    if 'Buddha' in english or 'Buddhism' in english or '寺' in chinese:
       return '佛教\tBuddhism'
    comm_keywords = ['Airlines', 'Bank', 'brand', 'CEO', 'Company', 'company',
                     'Corp.',
                     'Corporation', 'website']
    if EntryAnalyzer.check_keywords(comm_keywords, english):
      return '商务\tCommerce'
    com_sci_keywords = ['algorithm', 'byte', 'computer', 'computing', 'code',
                        'network', 'server', 'software']
    if EntryAnalyzer.check_keywords(com_sci_keywords, english):
      return '计算机科学\tComputer Science'
    drama_keywords = ['anime', 'film']
    if EntryAnalyzer.check_keywords(drama_keywords, english):
      return '戏剧\tDrama'
    education_keywords = ['University']
    if EntryAnalyzer.check_keywords(education_keywords, english):
      return '教育\tEducation'
    if (self.p_contains_16xx.match(english) or
        self.p_contains_17xx.match(english) or
        self.p_contains_18xx.match(english)):
      return '历史\tHistory'
    history_keywords = ['archaeological', 'Battle', 'Cultural Revolution',
                         'dynasty', '(history)',
                        'Incident', 'Khan', 'Mao']
    if (EntryAnalyzer.check_keywords(history_keywords, english)):
      return '历史\tHistory'
    if 'idiom' in english and len(chinese) == 4:
      return '成语\tIdiom'
    gov_keywords = ['Administration', 'Agency', 'bureau', 'Committee', 
                    'Commission', 'Department', 'Education',
                    'government',
                    'National',
                    'Patriotic', 'People\'s']
    if EntryAnalyzer.check_keywords(gov_keywords, english):
      return '政府\tGovernment'
    ling_keywords = ['linguistics', 'phonetics', 'phonology']
    if EntryAnalyzer.check_keywords(ling_keywords, english):
      return '语言学\tLinguistics'
    lit_chin_keywords = [ '(arch.)', 'archaic', '(classical)', '(literary)',
                          '(old)', '(old usage)']
    if EntryAnalyzer.check_keywords(lit_chin_keywords, english):
      return '文言文\tLiterary Chinese'
    literature_keywords = ['novelist', 'writer']
    if EntryAnalyzer.check_keywords(literature_keywords, english):
      return '文学\tLiterature'
    media_keywords = ['Publishing', 'Press', 'TV']
    if EntryAnalyzer.check_keywords(media_keywords, english):
      return '媒体\tMedia'
    place_keywords = ['capital ', ' city', 'City', 'county', 'County',
                      'Indonesia', 'Island', 'Lake',
                      'Macau', 'place in', 'River', 'Myanmar',
                      'town', 'UK', 'Vietnam']
    place_keywords_zh = ['庙', '湾', '区', '县', '镇']
    if (EntryAnalyzer.check_keywords(place_keywords, english) or
        EntryAnalyzer.check_keywords(place_keywords_zh, chinese)):
      return '地方\tPlaces'
    pol_keywords = ['politician', 'political']
    if EntryAnalyzer.check_keywords(pol_keywords, english):
      return '政治\tPolitics'
    if '(proverb)' in english:
      return '谚语\tProverb'
    if '(idiom)' in english and len(chinese) > 4:
      return '谚语\tProverb'
    if 'physicist' in english:
      return '机科学\tScience'
    return '现代汉语\tModern Chinese'

  def guess_entity_kind(entry: DictionaryEntry) -> str:
    """Guess the entity kind, default empty"""
    english = entry.english
    chinese = entry.simplified
    animal_keywords_zh = ['驼', '蟹', '猫', '狸', '獾', '猿']
    if EntryAnalyzer.check_keywords(animal_keywords_zh, chinese):
      return '动物\tAnimal'
    if 'novelist' in english:
      return '作者\tAuthor'
    if 'Bank' in english:
      return '银行\tBank'
    bird_keywords = ['bird species']
    bird_keywords_zh = ['鹭', '鸟', '鹉', '隼']
    if (EntryAnalyzer.check_keywords(bird_keywords, english) or
        EntryAnalyzer.check_keywords(bird_keywords_zh, chinese)):
       return '鸟\tBird'
    if 'constellation' in english:
       return '星座\tConstellation'
    company_keywords = ['Airlines', 'Company', 'company', 'Corp.',
                        'Corporation', 'Press',
                        'Publishing']
    if EntryAnalyzer.check_keywords(company_keywords, english):
       return '公司\tCompany'
    if 'district' in english or 'District' in english:
      return '地区\tDistrict'
    if ' city' in english or 'City' in english or 'capital' in english:
      return '城市\tCity'
    if 'county' in english or 'County' in english:
      return '县\tCounty'
    eth_keywords = ['ethnic group', 'ethnic minority']
    if EntryAnalyzer.check_keywords(eth_keywords, english):
      return '民族\tEthnic Group'
    if '(fish)' in english or 'shark' in english:
      return '鱼\tFish'
    if 'Islands' in english or '群岛' in chinese:
      return '群岛\tIslands'
    if 'Island' in english or '岛' in chinese:
      return '岛\tIsland'
    insect_keywords_zh = ['虫', '蛾', '蜂']
    if EntryAnalyzer.check_keywords(insect_keywords_zh, chinese):
      return '昆虫\tInsect'
    if 'Lake' in english:
      return '湖\tLake'
    if '(drug)' in english:
      return '药品\tMedication'
    if '(mineral)' in english:
      return '矿物\tMineral'
    if 'nebula' in english:
      return '星云\tNebula'
    person_keywords = ['activist', 'actor', 'adventurer', 'adviser',
                       'ambassador',
                       'artist',
                       'astronomer', 'author', 'brother', 'CEO', 'chemist',
                       'composer', 'dictator', 'diplomat', 'doctor',
                       'economist', 'educator',
                       'explorer',
                       'founder', 'inventor',
                       'Khan', 'leader', 'loyalist',
                       'mathematician', 'martyr', 'minister', 'missionary',
                       'officer',
                       'painter',
                       'person name',
                       'philosopher', 'pioneer', 'poet',
                       'physicist', 'psychologist', 'politician',
                       'president', 'psychiatrist', 'scientist', 'Secretary',
                       'sociologist', 'theorist', 'warlord',
                       'writer']
    if EntryAnalyzer.check_keywords(person_keywords, english):
      return '人\tPerson'
    place_keywords = ['Beijing', 'Indonesia', 'Macau', 'prefecture', 'place in',
                      'town', 'prefecture']
    place_keywords_zh = ['县', '庙', '镇']
    if (EntryAnalyzer.check_keywords(place_keywords, english) or
        EntryAnalyzer.check_keywords(place_keywords_zh, chinese)):
      return '地名\tPlace Name'
    if 'brand' in english:
       return '产品\tProduct'
    if 'River' in english:
      return '水名\tRiver'
    if 'surname' in english:
      return '姓氏\tSurname'
    if '寺' in chinese:
       return '寺庙\tTemple'
    if '栎' in chinese:
      return '树\tTree'
    if 'University' in english:
      return '大学\tUniversity'
    return '\\N\t\\N'

  def guess_grammar(chinese: str, english: str) -> str:
    """Guess what the part of speech is"""
    if len(english) > 0 and english[-1:] == '!':
      return 'interjection'
    if len(english) > 0 and english[0].isupper() and 'idiom' not in english:
      return 'proper noun'
    if '(onom.)' in english:
      return 'onomatopoeia'
    if '(interjection)' in english:
      return 'interjection'
    if len(chinese) > 4:
      return 'phrase'
    if len(chinese) == 4:
      return 'set phrase'
    if len(english) > 1 and english[:2] == 'a ':
      return 'noun'
    if len(english) > 2 and english[:3] == 'to ':
      return 'verb'
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
    return 'noun'

  def guess_subdomain(entry: DictionaryEntry) -> str:
    """Guess the term subdomain, default none, later check manually"""
    english = entry.english
    simplified = entry.simplified
    traditional = entry.traditional
    ag_keywords = ['agriculture', 'farming']
    if EntryAnalyzer.check_keywords(ag_keywords, english):
      return '农业\tAgriculture'
    arch_keywords = ['archeology', 'archaeology']
    if EntryAnalyzer.check_keywords(arch_keywords, english):
      return '考古学\tArchaeology'
    arts_keywords = ['(art)', 'fine arts']
    if EntryAnalyzer.check_keywords(arts_keywords, english):
      return '艺术\tArt'
    asia_keywords = ['Azerbaijan', 'Indonesia', 'Korean', 'Myanmar',
                     'Tajikistan', 'Vietnam']
    if EntryAnalyzer.check_keywords(asia_keywords, english):
      return '亚洲\tAsia'
    astrol_keywords = ['astrology', 'divination']
    if EntryAnalyzer.check_keywords(astrol_keywords, english):
      return '占星术\tAstrology'
    astr_keywords = ['astronomy', 'constellation', 'nebula', 'galaxy', '(star)']
    astr_keywords_zh = ['天文']
    if (EntryAnalyzer.check_keywords(astr_keywords, english) or
        EntryAnalyzer.check_keywords(astr_keywords_zh, simplified)):
      return '天文\tAstronomy'
    bio_keywords = ['bacteria', 'biology', '(cell)', 'chromosome', 'genetic',
                    'organism', 'osterone']
    bio_keywords_zh = ['胞', '脂肪']
    if (EntryAnalyzer.check_keywords(bio_keywords, english) or
         EntryAnalyzer.check_keywords(bio_keywords_zh, simplified)):
      return '生物学\tBiology'
    bot_keywords = ['botany']
    bot_keywords_zh = ['栎']
    if (EntryAnalyzer.check_keywords(bot_keywords, english) or
        EntryAnalyzer.check_keywords(bot_keywords_zh, simplified)):
      return '植物学\tBotany'
    chem_keywords = ['acid', 'C2', 'C3', 'C4', 'C5', 'alcohol', 'biochemistry',
                     'chemical', 'chemistry', 'chloride', 'fluoride', 'hydrate',
                     'lactose', 'molecular','oxide', 'sodium', 'sulfur']
    chem_keywords_zh = ['毒素']
    if (EntryAnalyzer.check_keywords(chem_keywords, english) or
        EntryAnalyzer.check_keywords(chem_keywords_zh, simplified)):
      return '化学\tChemistry'
    china_keywords = ['Anhui', 'Beijing', 'China', 'Chinese',
                      'Cultural Revolution', 'Fujian', 'Gansu',
                      'Guangdong',
                      'Guizhou', 'Guangxi',
                      'Hainan', 'Han dynasty',
                      'Hangzhou', 'Hebei', 'Heilongjiang', 'Henan',
                      'Hong Kong', 'Hubei', 'Hunan', 'Inner Mongolia',
                      'Jiangsu', 'Jiangxi', 'Jilin', 'Lhasa',
                      'Liaoning', 'Macau', 'Mao', 'Ningxia', 'PRC',
                      'Qing',
                      'Shandong', 'Shanxi',
                      'Shaanxi', 'Shanghai',
                      'Sichuan', 'Tianjin', 'Tibet', 'Xiamen', 'Xinjiang',
                      'Yunnan', 'Zhejiang']
    if EntryAnalyzer.check_keywords(china_keywords, english):
      return '中国\tChina'
    chin_med_keywords = ['acupuncture', '(Chinese medicine)', 'TCM']
    if EntryAnalyzer.check_keywords(chin_med_keywords, english):
      return '中医\tChinese Medicine'
    chr_keywords = ['Bible', 'biblical', 'Christian', '(Christian ceremony)',
                    'Testament']
    if EntryAnalyzer.check_keywords(chr_keywords, english):
      return '基督教\tChristianity'
    cloth_keywords_zh = ['裤', '衫', '襟', '裙', '鞋']
    if EntryAnalyzer.check_keywords(cloth_keywords_zh, simplified):
      return '服装\tClothing'
    dialect_keywords = ['Cantonese', 'dialect', 'erhua variant', 'Shanghainese']
    if EntryAnalyzer.check_keywords(dialect_keywords, english):
      return '方言\tDialect'
    econ__keywords = ['economics']
    if EntryAnalyzer.check_keywords(econ__keywords, english):
      return '经济\tEconomics'
    elec_keywords = ['circuit', '(electronics)', '(elec.)',
                     '(electrical engineering)', 'semiconductor']
    if EntryAnalyzer.check_keywords(elec_keywords, english):
      return '电子工程\tElectronic Engineering'
    eng_keywords = ['Britain', 'British', 'tEngland', 'English', 'London', 'UK']
    if EntryAnalyzer.check_keywords(eng_keywords, english):
      return '英国\tEngland'
    eu_keywords = ['Austrian', 'Czech', 'Dutch', 'France', 'French', 'German',
                   'Holland',
                   'Irish',
                   'Italian',
                   'Russian', 'Scottish',
                   'Soviet', 'Spanish', 'Swedish']
    if EntryAnalyzer.check_keywords(eu_keywords, english):
      return '欧洲\tEurope'
    fin_keywords = ['accountancy', 'accounting', 'finance']
    if EntryAnalyzer.check_keywords(fin_keywords, english):
      return '财会\tFinance and Accounting'
    food_keywords = ['cuisine', 'milk', ' sauce']
    food_keywords_zh = ['饼', '餐', '茶', '蛋糕', '葱', '果',  '酱', '酒',
                        '咖啡', '辣椒', '巧克力', '蒜', '汤', '土豆']
    food_keywords_zh_tw = ['麵']
    if (EntryAnalyzer.check_keywords(food_keywords, english) or
        EntryAnalyzer.check_keywords(food_keywords_zh, simplified) or
        EntryAnalyzer.check_keywords(food_keywords_zh_tw, traditional)):
      return '饮食\tFood and Drink'
    geog_keywords = ['geography', 'Islands', 'Ocean', 'ocean', 'peninsula']
    geog_keywords_zh = '岛'
    if (EntryAnalyzer.check_keywords(geog_keywords, english) or 
        EntryAnalyzer.check_keywords(geog_keywords_zh, simplified)):
      return '地理\tGeography'
    geo_keywords = ['geological', 'geology', 'mineral']
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
    japan_keywords = ['Japan']
    if EntryAnalyzer.check_keywords(japan_keywords, english):
      return '日本\tJapan'
    law_keywords = ['criminal', 'judicial', '(law)']
    law_keywords_zh = ['法官', '律师']
    if (EntryAnalyzer.check_keywords(law_keywords, english) or
        EntryAnalyzer.check_keywords(law_keywords_zh, simplified)):
      return '法律\tLaw'
    martial_keywords = ['Martial Art']
    if EntryAnalyzer.check_keywords(martial_keywords, english):
      return '武术\tMartial Arts'
    math_keywords = ['algebra', 'calculus', 'equation', 'math']
    math_keywords_zh = ['函数']
    if (EntryAnalyzer.check_keywords(math_keywords, english) or
        EntryAnalyzer.check_keywords(math_keywords_zh, simplified)):
      return '数学\tMathematics'
    med_keywords = ['anatomy', 'cancer', 'coronary', 'disease', 'disorder',
                    '(drug)', 'erosis', 'fever', 'itis', 'medical', 'medicine',
                    '(med.)', 'paralysis', 'psychiatry', 'physiology',
                    'surgery', 'syndrome', 'therapy', 'vaccine', 'virus']
    med_keywords_zh = ['病', '激素', '炎', '症']
    if (EntryAnalyzer.check_keywords(med_keywords, english) or
        EntryAnalyzer.check_keywords(med_keywords_zh, simplified)):
      return '医学\tMedicine'
    mil_keywords = ['bomb' , 'military', 'missile', 'warfare', 'warship']
    if EntryAnalyzer.check_keywords(mil_keywords, english):
      return '军事\tMilitary'
    music_keywords = ['guitar', 'music', '(opera)']
    music_keywords_zh = ['歌', '琴', '樂器']
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
    pal_keywords = ['dinosaur', 'fossil', 'paleo', 'saurus']
    if EntryAnalyzer.check_keywords(pal_keywords, english):
      return '古生物学\tPaleontology'
    phon_keywords = ['phonetics']
    if EntryAnalyzer.check_keywords(phon_keywords, english):
      return '语音学\tPhonetics'
    photo_keywords = ['photography']
    if EntryAnalyzer.check_keywords(photo_keywords, english):
      return '摄影术\tPhotography'
    pol_keywords = ['political', '(politics)']
    if EntryAnalyzer.check_keywords(pol_keywords, english):
      return '政治\tPolitics'
    pysc_keywords = ['(psych.)', 'psychology']
    if EntryAnalyzer.check_keywords(pysc_keywords, english):
      return '心理学\tPsychology'
    phys_keywords = ['(cosmology)', '(mechanics)', 'physics', 'thermodynamics']
    if EntryAnalyzer.check_keywords(phys_keywords, english):
      return '物理\tPhysics'
    rel_keywords = ['religion']
    if EntryAnalyzer.check_keywords(rel_keywords, english):
      return '宗教\tReligion'
    slang_keywords = ['curse', 'netspeak', 'slang']
    if EntryAnalyzer.check_keywords(slang_keywords, english):
      return '俚语\tSlang'
    space_keywords_zh = ['航天', '宇航']
    if EntryAnalyzer.check_keywords(space_keywords_zh, simplified):
      return '航天\tSpace Flight'
    spok_keywords = ['(coll.)' '(colloquial)']
    if EntryAnalyzer.check_keywords(spok_keywords, english):
      return '口语\tSpoken Language'
    sport_keywords = ['(athletics)', 'baseball', 'basketball', 'boxing',
                      'football', '(golf)', 'gymnastics', 'soccer', ' sport']
    if EntryAnalyzer.check_keywords(sport_keywords, english):
      return '体育\tSport'
    stats_keywords = ['statistics']
    if EntryAnalyzer.check_keywords(stats_keywords, english):
      return '统计学\tStatistics'
    us_keywords = ['America', 'state', 'Pennsylvania', 'US']
    if EntryAnalyzer.check_keywords(us_keywords, english):
      return '美国\tUnited States'
    zoo_keywords = ['bird family', 'bird species', '(fish)', 'whale', 'shark',
                    'zoology']
    zoo_keywords_zh = ['猫', '虫', '隼', '蛾', '蜂', '蟹', '鹭', '狸', '鸟', 
                       '驼', '鹉', '獾', '鲨', '猿']
    if (EntryAnalyzer.check_keywords(zoo_keywords, english) or
        EntryAnalyzer.check_keywords(zoo_keywords_zh, simplified)):
      return '动物学\tZoology'
    return '\\N\t\\N'

  def ignore(entry: DictionaryEntry) -> bool:
    traditional = entry.traditional
    english = entry.english
    if 'erhua variant' in english:
      return True
    ignore_words = ['皇太後', '入團', '麵的', '正太']
    if EntryAnalyzer.check_keywords(ignore_words, traditional):
      return True
    else:
      return False

  def is_modern_named_entity(self, entry: DictionaryEntry) -> bool:
    """Guess whether the term is a modern named entity"""
    chinese = entry.simplified
    english = entry.english
    if 'idiom' in entry.english:
      return False
    if (self.p_contains_16xx.match(english) or
        self.p_contains_17xx.match(english) or
        self.p_contains_18xx.match(english)):
      return False
    if self.p_contains_19xx.match(english):
      return True
    if self.p_contains_2xxx.match(english):
      return True
    entity_keywords = ['actress', 'Administration', 'Afghan', 'Airlines',
                       'Albania', 'Algeria',
                       'Angola', 'America',
                       'anime', 'Anguilla',
                       'Australia', 'Austria', 'Bahamas', 'Bahrain',
                       'basketball player', 'Belgian', 'brand',
                       'Brazil', 'British', 'Business', 'Cameroon',
                       'Canadian',
                       'Canada', 'Cape Verde', 'capital of', 'Caribbean',
                       'Carolina', 'Catholic', 'Chapel', 'character', 
                       'Chinese diplomat', 'Chinese politician',  'Club',
                       'Colorado', 'Colombia', 'Commission', 'Company',
                       'company', 'comic', 'Corporation',
                       'corporation', 'Council', 'Croatia',
                       'Cuba', 'Cyprus',
                       'Czech', 'Dominica', 'Dutch', 'Egypt',
                       'England', 'English', 'Ethiopia', 'Europe',
                       'female singer',
                       'film director', 'Film Festival', 'Finland',
                       'football player',
                       'France', 'French', 'Gambia', 'German', 'given name',
                       'Greece', 'Greek', 'Group', 'Guomindang',
                       'Harry Potter',
                       'Hawaii', 'HK-born', 'Hong Kong actor',
                       'Holland', 'hotel chain', 'Hungarian',
                       'Idaho',
                       'Iowa',
                       'Iran', 'Iraq', 'Ireland', 'Israel',  'Italy',
                       'Jewish', 'Journal', 'journalist and writer',
                       'Kansas', 'Kenya',
                       'Kiribati',
                       'Kyrgyzstan', 'male name',
                       '(name)', 'Lebanon', 'Lesotho', 'London',
                       'Manhattan',
                       'manufacturer', 'Mecca',
                       'Mexican', 'Ministry', 'Morocco', 'Mozambique', 'NBA',
                       'Netherlands',
                       'Nevada', 'New Caledonia',
                       'New York', 'New Zealand', 'Nicaragua', 'Niger',
                       'Norway', 'Palestine', 'Palestinian', 'Paris', 'Party',
                       'performing artist',
                       'person name', 'PLA', 'Poland', 'pop idol', 'pop singer',
                       'pop star', 'Portugal',
                       'proper name',
                       'Pennsylvania', 'Philippine', 'PRC', 'Qatar', 'Russia',
                       'Rwanda',
                       'Saudi Arabia',
                       'Scotland', 'singer-songwriter', 'singer and actor',
                       'South Africa', 'Spain',
                       'Sudan',  'supermarket', 'surname', 'Sweden', 'Swiss',
                       'Switzerland', 'Syria', 'Taiwanese politician',
                       'Tanzania', 'Tokyo', 'Turkey', 'United States',
                       '(U.S.)', 'US', 'UK', 'TV',
                       'Ukraine', 'University', 'Uzbekistan', 'Venice',
                       'video game',
                       'website', 'Wyoming', 'Zambia', 'Zimbabwe']
    entity_keywords_zh = ['·']
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
  luid = 164613
  with open(out_fname, 'w') as out_file:
    for trad, entry in cedict.items():
      if trad not in cnotes_dict:
        entry_analysis = summary.increment_absent_dict2(entry)
        if (sample < 100
            and not entry_analysis.contains_alphanum
            and len(trad) > 1
            #and not entry_analysis.contains_notes
            and not len(entry.senses) > 1
            and not entry_analysis.refers_to_variant
            and not entry_analysis.is_modern_named_entity
            and not entry_analysis.ignore
            #and not entry_analysis.contains_punctuation
          ):
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
