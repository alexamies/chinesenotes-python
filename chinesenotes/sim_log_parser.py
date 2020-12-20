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
Methods for parsing chinesenotes-go web app logs including similarity results.

The logs have JSON format with GCP fields for Cloud Run assumed to be in
directory 'logs'. They are generated with GCP Cloud Logging, exported to a 
Log Sink in a GCS bucket and downloaded to the local drive.
"""

import _csv
import csv
import json
import logging
import os
from os import path
from pathlib import Path

LOG_PATH = 'logs'


def parse_logs():
  """Parses the logs"""
  logging.info('parse_logs enter')
  p = Path.cwd() / LOG_PATH
  fnames = p.glob('*.json')
  with open('data/sim_training.csv', 'w', newline='') as outF:
    csvOut = csv.writer(outF)
    csvOut.writerow(['Query', 'Rank', 'Term', 'Pinyin Match', 'In Notes',
                    'Unigram Count', 'Hamming', 'Is Substring'])
    for fname in fnames:
      process_log(csvOut, fname)


def process_log(csvOut: _csv.writer, fname: str):
  """Process a single log file."""
  f = open(fname)
  lines = f.readlines()
  for line in lines:
    logObj = json.loads(line)
    payload = logObj['textPayload']
    parts = payload.split(':')
    if len(parts) > 1:
      data = parts[-1]
      values = data.split(',')
      if len(values) > 7:
        query = values[0].strip()
        rank = int(values[1]) + 1
        term = values[2].strip()
        pMatch = int(values[3])
        inNotes = int(values[4])
        uniCount = int(values[5])
        hamming = int(values[6])
        isSubstring = int(values[7])
        csvOut.writerow([query, rank, term, pMatch, inNotes, uniCount, hamming,
                        isSubstring])


def main():
  """Command line entry point"""
  logging.basicConfig(level=logging.INFO)
  logging.info('Parsing logs')
  parse_logs()


# Entry point from a script
if __name__ == '__main__':
  main()
