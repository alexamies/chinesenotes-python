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
import codecs
import logging
import os
import sys
import urllib.request


def Greedy(wdict, chunk):
  """A greedy tokenizer"""
  segments = []
  i = 0
  while i < len(chunk):
    for j in range(len(chunk), -1, -1):
      w = chunk[i:j]
      if w in wdict:
        segments.append(w)
        i += len(w)
        break
      elif len(w) == 1:
        segments.append(w)
        i += 1
        break
  return segments


def Lookup(wdict, keyword):
  """Looks up the keyword in the dictionary
  """
  entry = None
  if keyword in wdict:
    entry = wdict[keyword]
    logging.info("{}".format(entry["english"]))
  else:
    logging.info("No entry for {}".format(keyword))
  return entry


def OpenDictionary(fname, chineseOnly = False):
  """Reads the dictionary from a file or URL.

    Set chineseOnly = True if you are only using the dictionary to segment
    Chinese text. This will decrease the memory needed.

    Args:
      fname: the file or remote URL to read the dictionary from
      chineseOnly: Only include Chinese and no other filds
    Returns:
      A dictionary object
  """
  logging.info("Opening the Chinese Notes dictionary from {}".format(fname))
  if fname.startswith('https'):
    wdict = load_from_url(fname, chineseOnly)
  else:
    wdict = load_locally(fname, chineseOnly)
  logging.info("OpenDictionary completed with %d entries" % len(wdict))
  return wdict


def load_from_url(url, chineseOnly = False):
  """Reads the dictionary from a local file
  """
  logging.info("Opening the dictionary remotely")
  wdict = {}
  with urllib.request.urlopen(url) as f:
    data = f.read().decode('utf-8')
    wdict = read_dict(data.splitlines(), chineseOnly)
  return wdict

def load_locally(fname, chineseOnly = False):
  """Reads the dictionary from a local file
  """
  logging.info("Opening the dictionary from a local file")
  wdict = {}
  with codecs.open(fname, 'r', "utf-8") as f:
    wdict = read_dict(f, chineseOnly)
  return wdict

def read_dict(f, chineseOnly = False):
  """Reads the dictionary from a file object into memory
  """
  wdict = {}
  for line in f:
    line = line.strip()
    if not line:
      continue
    fields = line.split('\t')
    if fields and len(fields) >= 10:
      entry = {}
      traditional = fields[2]
      entry['traditional'] = traditional
      entry['simplified'] = fields[1]
      if not chineseOnly:
        entry['id'] = fields[0]
        entry['pinyin'] = fields[3]
        entry['english'] = fields[4]
        entry['grammar'] = fields[5]
        if fields and len(fields) >= 15 and fields[14] != '\\N':
          entry['notes'] = fields[14]
      key = entry['simplified']
      if key not in wdict:
        entry['other_entries'] = []
        wdict[key] = entry
        if traditional != '\\N':
          wdict[traditional] = entry
      else:
        wdict[key]['other_entries'].append(entry)
        if traditional != '\\N':
          if traditional in wdict:
            wdict[traditional]['other_entries'].append(entry)
          else:
            entry['other_entries'] = []
            wdict[traditional] = entry
  return wdict


def main():
  logging.basicConfig(level=logging.INFO)
  cn_home = "https://github.com/alexamies/chinesenotes.com"
  fname = "{}/blob/master/data/words.txt?raw=true".format(cn_home)
  if "CNREADER_HOME" in os.environ:
    cn_home = os.environ["CNREADER_HOME"]
    fname = "{}/data/words.txt".format(cn_home)
  wdict = OpenDictionary(fname)
  parser = argparse.ArgumentParser()
  parser.add_argument('--lookup',
                      dest='lookup',
                      help='Lookup a word')
  parser.add_argument('--tokenize',
                      dest='tokenize',
                      help='Segment the text into multi-character terms')
  args = parser.parse_args()
  if args.lookup:
    entry = Lookup(wdict, args.lookup)
    print("English: {}".format(entry["english"]))
  elif args.tokenize:
    logging.info("Greedy dictionary-based text segmentation")
    segments = Greedy(wdict, args.tokenize)
    print("Segments: {}".format(segments))

# Entry point from a script
if __name__ == "__main__":
  main()