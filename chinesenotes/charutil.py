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
Utility for converting traditional to simplified and Pinyin
"""

def to_simplified(wdict, trad):
  """Convert to simplified Chinese characters"""
  simplified = ""
  traditional = trad
  pinyin = []
  for char in trad:
    if char in wdict:
      entry = wdict[char]
      simplified += entry.simplified
      pinyin.append(entry.senses[0].pinyin)
    else:
      simplified += char
      pinyin.append(' ')
  if simplified == trad:
    traditional = '\\N'
  pinyin_str = ''.join(pinyin)
  if len(trad) > 3: # For phrases add space in between syllables
    pinyin_str = ' '.join(pinyin)
  return simplified, traditional, pinyin_str.lower()


def to_traditional(wdict, chinese):
  """Convert to traditional Chinese characters"""
  traditional = ''
  for char in chinese:
    if char in wdict:
      entry = wdict[char]
      simplified = entry.simplified
      trad = entry.traditional
      if trad == "\\N":
        trad = simplified
      traditional += trad
    else:
      traditional += char
  return traditional
