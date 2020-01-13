# -*- coding: utf-8 -*-
"""
Utility for segmenting text
"""
from cndict import OpenDictionary
import argparse
import logging
import os
import sys


def Greedy(wdict, chunk):
  segments = []
  logging.info("Greedy dictionary-based text segmentation")
  logging.info("Chunk: {}".format(chunk))
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
  logging.info("Segments: {}".format(segments))


# Basic test
def main():
  if os.environ.get("CNREADER_HOME") is None:
    print("CNREADER_HOME is not defined")
    sys.exit(1)
  logging.basicConfig(level=logging.INFO)
  cn_home = os.environ["CNREADER_HOME"]
  fname = "{}/data/words.txt".format(cn_home)
  wdict = OpenDictionary(fname)
  parser = argparse.ArgumentParser()
  parser.add_argument("chunk")
  args = parser.parse_args()
  Greedy(wdict, args.chunk)


if __name__ == "__main__":
  main()