# -*- coding: utf-8 -*-
"""
Utility for converting traditional to simplified and Pinyin
"""
from cndict import OpenDictionary
import os
import sys

def ToSimplified(wdict, trad):
  simplified = u""
  traditional = trad
  pinyin = u""
  for t in trad:
    if t in wdict:
      entry = wdict[t]
      simplified += entry['simplified']
      pinyin += entry['pinyin']
    else:
      simplified += t
      pinyin += ' '
  if simplified == trad:
    traditional = "\\N"
  return simplified, traditional, pinyin.lower()


def ToTraditional(wdict, chinese):
  traditional = u""
  for c in chinese:
    if c in wdict:
      entry = wdict[c]
      s = entry['simplified']
      t = entry['traditional']
      if t ==  "\\N":
        t = s
      traditional += t
  return traditional

# Basic test
def main():
  if os.environ.get("CNREADER_HOME") is None:
    print("CNREADER_HOME is not defined")
    sys.exit(1)
  cn_home = os.environ["CNREADER_HOME"]
  fname = "{}/data/words.txt".format(cn_home)
  wdict = OpenDictionary(fname)
  trad = u"四種廣說"
  print("Test ToSimplified({})".format(trad))
  s, t, p = ToSimplified(wdict, trad)
  print(u"Simplified: {}".format(s))

  simplified = u"操作系统"
  print("Test ToTraditional({})".format(simplified))
  traditional = ToTraditional(wdict, simplified)
  print(u"Traditional: %s" % traditional)



if __name__ == "__main__":
  main()