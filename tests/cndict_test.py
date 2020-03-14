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
Unit tests for chinesenotes.cndict
"""

import io
import unittest

from chinesenotes import cndict

class TestCNDict(unittest.TestCase):

  def test_greedy(self):
    """Empty dictionary"""
    trad = '四種廣說'
    wdict = {}
    segments = cndict.tokenize_greedy(wdict, trad)
    self.assertEqual(len(segments), len(trad))

  def test_load_dictionary0(self):
    """Empty dictionary"""
    trad = '說'
    luid = '1'
    hwid = '1'
    simplified = '说'
    pinyin = 'shuō'
    english = 'say'
    grammar = 'say'
    nn = '\\N\t\\N'
    note = 'hello'
    line = (f'{luid}\t{simplified}\t{trad}\t{pinyin}\t{english}\t{grammar}\t'
             '{nn}\t{nn}\t{nn}\t{nn}\t{note}\t{hwid}\n')
    dict_file = io.StringIO(line)
    wdict = {}
    wdict = cndict._load_dictionary(dict_file)
    self.assertEqual(len(wdict), 2) # Indexed both by simplified and traditional
    entry = wdict[trad]
    self.assertEqual(entry.simplified, simplified)
    self.assertEqual(entry.pinyin, pinyin)
    self.assertEqual(entry.english, english)


if __name__ == '__main__':
    unittest.main()
