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

"""Type definitions for the Chinese Notes Reader dictionary
"""

from typing import List


class WordSense:
  """Represents a word sense"""

  def __init__(self,
               simplified: str,
               traditional: str,
               pinyin: str,
               english: str):
    """Constructor"""
    self._simplified = simplified
    self._traditional = traditional
    self._pinyin = pinyin
    self._english = english
    self._grammar = None
    self._notes = None

  @property
  def english(self) -> str:
    """English equivalents separate by a delimiter if more than one"""
    return self._english

  @property
  def grammar(self) -> str: # pylint: disable=function-redefined
    """Part of speech for the word sense"""
    return self._grammar

  @grammar.setter
  def grammar(self, grammar: str):
    """Sets part of speech for the word sense"""
    self._grammar = grammar

  @property
  def notes(self) -> str:
    """General notes including references for the word sense"""
    return self._notes

  @notes.setter
  def notes(self, value: str):
    """Sets general notes including references for the word sense"""
    self._notes = value

  @property
  def pinyin(self) -> str: # pylint: disable=function-redefined
    """Pronunciation using pinyin representation"""
    return self._pinyin

  @property
  def simplified(self) -> str: # pylint: disable=function-redefined
    """Simplified Chinese representation"""
    return self._simplified

  @property
  def traditional(self) -> str: # pylint: disable=function-redefined
    """Traditional Chinese representation"""
    return self._traditional

class DictionaryEntry:
  """Represents an entry in the Chinese-English dictionary"""

  def __init__(self, headword: str, senses: List[WordSense], headword_id: str):
    """Constructor"""
    self._headword = headword
    self._senses = senses
    self._headword_id = headword_id

  def add_word_sense(self, sense: WordSense):
    """Add another word sense to this headword"""
    self._senses.append(sense)

  @property
  def headword(self) -> str:
    """The Chinese headword that the entry describes"""
    return self._headword

  @property
  def headword_id(self) -> str:
    """A unique identifier for the entry"""
    return self._headword_id

  @property
  def senses(self) -> List[WordSense]:
    """A list of senses for the entry"""
    return self._senses
