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
Unit tests for chinesenotes.cndict_types
"""

import unittest

from chinesenotes import cndict_types

class DictionaryEntryTest(unittest.TestCase):

  def test_add_word_sense(self):
    """Add a new sense to a DictionaryEntry object"""
    trad = '說'
    hwid = '1'
    entry = cndict_types.DictionaryEntry(trad, [], hwid)
    simplified = '说'
    pinyin = 'shuō'
    english = 'say'
    sense = cndict_types.WordSense(simplified, trad, pinyin, english)
    entry.add_word_sense(sense)
    senses = entry.senses
    self.assertEqual(len(senses), 1)


class WordSenseTest(unittest.TestCase):

  def test_english(self):
    """Add a new sense to a DictionaryEntry object"""
    trad = '說'
    simplified = '说'
    pinyin = 'shuō'
    english = 'say'
    sense = cndict_types.WordSense(simplified, trad, pinyin, english)
    self.assertEqual(sense.english, english)

  def test_notes(self):
    """Add a new sense to a DictionaryEntry object"""
    trad = '說'
    simplified = '说'
    pinyin = 'shuō'
    english = 'say'
    sense = cndict_types.WordSense(simplified, trad, pinyin, english)
    notes = 'say something'
    sense.notes = notes
    self.assertEqual(sense.notes, notes)


if __name__ == '__main__':
    unittest.main()
