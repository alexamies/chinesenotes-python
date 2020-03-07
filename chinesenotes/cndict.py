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
import urllib.request
from typing import List, Mapping, Union

def greedy(wdict: Mapping[str, Mapping[str, str]], chunk: str) -> List[str]:
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


def lookup(wdict: Mapping[str, Mapping[str, Union[List[dict], str]]],
           keyword: str) -> Mapping[str, Union[List[dict], str]]:
  """Looks up the keyword in the dictionary or return None if it is not there
  """
  return wdict[keyword]


def open_dictionary(fname: str,
                    chinese_only=False) -> Mapping[str, Mapping[str, Union[List[dict], str]]]:
  """Reads the dictionary from a file or URL.

    Set chinese_only = True if you are only using the dictionary to segment
    Chinese text. This will decrease the memory needed.

    Args:
      fname: the file or remote URL to read the dictionary from
      chinese_only: Only include Chinese and no other filds
    Returns:
      A dictionary object
  """
  logging.info("Opening the Chinese Notes dictionary from %s", fname)
  if fname.startswith('https'):
    wdict = _load_from_url(fname, chinese_only)
  else:
    wdict = _load_locally(fname, chinese_only)
  logging.info("open_dictionary completed with %d entries", len(wdict))
  return wdict


def _load_from_url(url: str,
                   chinese_only=False) -> Mapping[str, Mapping[str, Union[List[dict], str]]]:
  """Reads the dictionary from a local file
  """
  logging.info("Opening the dictionary remotely")
  wdict = {}
  with urllib.request.urlopen(url) as dict_file:
    data = dict_file.read().decode('utf-8')
    wdict = _read_dict(data.splitlines(), chinese_only)
  return wdict

def _load_locally(fname: str,
                  chinese_only=False) -> Mapping[str, Mapping[str, Union[List[dict], str]]]:
  """Reads the dictionary from a local file
  """
  logging.info("Opening the dictionary from a local file")
  wdict = {}
  with codecs.open(fname, 'r', "utf-8") as dict_file:
    wdict = _read_dict(dict_file, chinese_only)
  return wdict

def _read_dict(dict_file: codecs.StreamReaderWriter,
               chinese_only=False) -> Mapping[str, Mapping[str, Union[List[dict], str]]]:
  """Reads the dictionary from a file object into memory
  """
  wdict = {}
  for line in dict_file:
    line = line.strip()
    if not line:
      continue
    fields = line.split('\t')
    if fields and len(fields) >= 10:
      entry = {}
      traditional = fields[2]
      entry['traditional'] = traditional
      entry['simplified'] = fields[1]
      if not chinese_only:
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
  """Command line entry point"""
  logging.basicConfig(level=logging.INFO)
  cn_home = "https://github.com/alexamies/chinesenotes.com"
  fname = "{}/blob/master/data/words.txt?raw=true".format(cn_home)
  if "CNREADER_HOME" in os.environ:
    cn_home = os.environ["CNREADER_HOME"]
    fname = "{}/data/words.txt".format(cn_home)
  wdict = open_dictionary(fname)
  parser = argparse.ArgumentParser()
  parser.add_argument('--lookup',
                      dest='lookup',
                      help='Lookup a word')
  parser.add_argument('--tokenize',
                      dest='tokenize',
                      help='Segment the text into multi-character terms')
  args = parser.parse_args()
  if args.lookup:
    entry = lookup(wdict, args.lookup)
    print("English: {}".format(entry["english"]))
  elif args.tokenize:
    logging.info("Greedy dictionary-based text segmentation")
    segments = greedy(wdict, args.tokenize)
    print("Segments: {}".format(segments))

# Entry point from a script
if __name__ == "__main__":
  main()
