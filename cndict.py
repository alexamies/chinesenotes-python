# -*- coding: utf-8 -*-
"""
Utility loads the Chinese Notes Reader dictionary into a Python dictionary.

Simplified and traditional words are keys.
"""
import argparse
import codecs
import logging
import os
import sys


def Lookup(wdict, keyword):
  """Looks up the keyword in the dictionary
  """
  entry = {}
  if keyword in wdict:
    entry = wdict[keyword]
    logging.info("{}".format(entry["english"]))
  else:
    logging.info("No entry for {}".format(keyword))
  return entry


def OpenDictionary(fname):
  """Reads the dictionary into memory
  """
  logging.info("Opening the Chinese Notes Reader dictionary")
  wdict = {}
  with codecs.open(fname, 'r', "utf-8") as f:
    for line in f:
      line = line.strip()
      if not line:
        continue
      fields = line.split('\t')
      if fields and len(fields) >= 10:
        entry = {}
        entry['id'] = fields[0]
        entry['simplified'] = fields[1]
        entry['traditional'] = fields[2]
        entry['pinyin'] = fields[3]
        entry['english'] = fields[4]
        entry['grammar'] = fields[5]
        if fields and len(fields) >= 15 and fields[14] != '\\N':
          entry['notes'] = fields[14]
        traditional = entry['traditional']
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
  logging.info("OpenDictionary completed with %d entries" % len(wdict))
  return wdict


def main():
  if os.environ.get("CNREADER_HOME") is None:
    print("CNREADER_HOME is not defined")
    sys.exit(1)
  logging.basicConfig(level=logging.INFO)
  cn_home = os.environ["CNREADER_HOME"]
  fname = "{}/data/words.txt".format(cn_home)
  wdict = OpenDictionary(fname)
  parser = argparse.ArgumentParser()
  parser.add_argument("lookup")
  args = parser.parse_args()
  Lookup(wdict, args.lookup)


# Entry point from a script
if __name__ == "__main__":
  main()