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
Unit tests for chinesenotes.charutils
"""

import unittest

from chinesenotes import charutil

class TestCharutil(unittest.TestCase):

  def test_to_simplified0(self):
    """Empty dictionary"""
    trad = '四種廣說'
    wdict = {}
    simplified, _, _ = charutil.to_simplified(wdict, trad)
    self.assertEqual(simplified, trad)

  def test_to_traditional0(self):
    """Empty dictionary"""
    simplified = '操作系统'
    wdict = {}
    trad = charutil.to_traditional(wdict, simplified)
    self.assertEqual(simplified, trad)


if __name__ == '__main__':
    unittest.main()
