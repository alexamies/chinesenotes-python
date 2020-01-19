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

"""A character counting pipeline."""

from __future__ import absolute_import

import argparse
import logging
import re

from past.builtins import unicode

import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.metrics import Metrics
from apache_beam.metrics.metric import MetricsFilter
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions


class CharExtractingDoFn(beam.DoFn):
  """Parse each line of input text into characters."""

  def __init__(self):
    beam.DoFn.__init__(self)
    self.char_counter = Metrics.counter(self.__class__, 'chars')

  def process(self, element):
    """Returns an iterator over the characters of this element.
    Args:
      element: a line of text
    Returns:
      A list of characters
    """
    line = element.strip()
    chars = []
    for c in line:
      if ord(c) > 128:
        chars.append(c)
        self.char_counter.inc()
    return chars


def load_ignore(fname):
  """Loads patterns signalling lines to ignore
    Args:
      fname: File name containing patterns
    Returns:
      A list of patterns
  """
  values = []
  with open(fname, 'r') as f:
    lines = f.readlines()
    for line in lines:
      values.append(line.rstrip('\n'))
  return values


def run(argv=None, save_main_session=True):
  """Main entry point to pipeline."""
  parser = argparse.ArgumentParser()
  parser.add_argument('--corpus_home',
                      dest='corpus_home',
                      help='Provide either corpus home or single input file')
  parser.add_argument('--input',
                      dest='input',
                      help='Provide either corpus home or single input file')
  parser.add_argument('--ignorelines',
                      dest='ignorelines',
                      help='Ignore lines containing these words')
  parser.add_argument('--output',
                      dest='output',
                      required=True,
                      help='Output file')
  known_args, pipeline_args = parser.parse_known_args(argv)
  pipeline_options = PipelineOptions(pipeline_args)
  pipeline_options.view_as(SetupOptions).save_main_session = save_main_session
  p = beam.Pipeline(options=pipeline_options)
  ignorepatterns = []
  if known_args.ignorelines:
    ignorepatterns = load_ignore(known_args.ignorelines)
  if known_args.corpus_home:
    logging.info('corpus_home: %s', known_args.corpus_home)
    fName = '{}/data/corpus/collections.csv'.format(known_args.corpus_home)
    lines = p | 'read' >> ReadFromText(fName)
  else:
    lines = p | 'read' >> ReadFromText(known_args.input)

  # Count the occurrences of each character.
  def count_ones(char_ones):
    (c, ones) = char_ones
    return (c, sum(ones))

  # Ignore counts for lines that are boilerplate (copyright notices, etc)
  re_patterns = []
  for val in ignorepatterns:
    pat = '.*{}.*'.format(val)
    re_patterns.append(re.compile(pat, re.IGNORECASE))

  def not_boilerplate(line):
    """true if the line does not match a boilerplate pattern """
    for re_pattern in re_patterns:
      if re_pattern.match(line) != None:
        return False
    return True

  counts = (lines
            | 'filter' >> beam.Filter(not_boilerplate)
            | 'split' >> (beam.ParDo(CharExtractingDoFn())
                          .with_output_types(unicode))
            | 'pair_with_one' >> beam.Map(lambda x: (x, 1))
            | 'group' >> beam.GroupByKey()
            | 'count' >> beam.Map(count_ones))

  # Format the result
  def format_result(char_count):
    (c, count) = char_count
    return '%s\t%d' % (c, count)

  output = counts | 'format' >> beam.Map(format_result)

  output | 'write' >> WriteToText(known_args.output)
  result = p.run()
  result.wait_until_finish()
  if (not hasattr(result, 'has_job') or result.has_job):
    chars_count_filter = MetricsFilter().with_name('chars')
    query_result = result.metrics().query(chars_count_filter)
    if query_result['counters']:
      chars_counter = query_result['counters'][0]
      logging.info('Total chars: %d', chars_counter.result)

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
run()