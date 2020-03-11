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
Command line utility for processing Chinese text
"""

import argparse
import os
from chinesenotes import charutil, cndict


def main():
  """For use from command line"""
  cn_home = "https://github.com/alexamies/chinesenotes.com"
  fname = "{}/blob/master/data/words.txt?raw=true".format(cn_home)
  if "CNREADER_HOME" in os.environ:
    cn_home = os.environ["CNREADER_HOME"]
    fname = "{}/data/words.txt".format(cn_home)
  wdict = cndict.open_dictionary(fname)
  parser = argparse.ArgumentParser()
  parser.add_argument('--tosimplified',
                      dest='tosimplified',
                      help='Convert the given traditional text to simplified')
  parser.add_argument('--totraditional',
                      dest='totraditional',
                      help='Convert the given simplified text to traditional')
  parser.add_argument('--topinyin',
                      dest='topinyin',
                      help='Convert the given text to topinyin')
  args = parser.parse_args()
  if args.tosimplified:
    simplified, _, _ = charutil.to_simplified(wdict, args.tosimplified)
    print(u"Simplified: {}".format(simplified))
  elif args.totraditional:
    trad = charutil.to_traditional(wdict, args.totraditional)
    print(u"Traditional: %s" % trad)
  elif args.topinyin:
    _, _, pinyin = charutil.to_simplified(wdict, args.topinyin)
    print(u"Pinyin: {}".format(pinyin))


# Command line entry point
if __name__ == "__main__":
  main()
