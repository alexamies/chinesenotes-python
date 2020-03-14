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

"""A term frequency pipeline for Chinese text.

Counts terms, including multi-word expressions, based on a dictionary tokenizer
over a corpus of Chinese text.
"""

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
from apache_beam.io.textio import ReadAllFromText


from chinesenotes import cndict


class TermExtractingDoFn(beam.DoFn):
  """Parse each line of input text into multi-character terms."""

  def __init__(self):
    beam.DoFn.__init__(self)
    cn_home = "https://github.com/alexamies/chinesenotes.com"
    fname = "{}/blob/master/data/words.txt?raw=true".format(cn_home)
    self.wdict = cndict.open_dictionary(fname, True)
    self.term_counter = Metrics.counter(self.__class__, 'terms')

  def process(self, element):
    """Returns an iterator over the tokens of this oine of text.
    Args:
      element: a line of text
    Returns:
      A list of tokens
    """
    line = element.strip()
    terms = cndict.tokenize_greedy(self.wdict, line)
    self.term_counter.inc(len(terms))
    return terms


class ExtractIndexEntry(beam.DoFn):
  """Reads a line of an index file"""

  def __init__(self):
    beam.DoFn.__init__(self)
    self.file_counter = Metrics.counter(self.__class__, 'files')
    
  def process(self, element):
    """Returns the first field, which is the file name, if not a comment"""
    fields = element.split('\t')
    fnames = []
    if len(fields) > 0 and not fields[0].startswith('#'):
      fnames.append(fields[0])
      self.file_counter.inc()
    return fnames


def add_prefix(fname, dname = ''):
  """Combines directory and file name"""
  path = fname
  if dname:
    path = '{}/{}'.format(dname, fname)
  yield path


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
                      help='The directory or bucke of the corpus home')
  parser.add_argument('--input',
                      dest='input',
                      help='A single input file')
  parser.add_argument('--corpus_prefix',
                      dest='corpus_prefix',
                      help='Prefix after corpus home where the files are')
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
    corpus_data_dir = '{}/data/corpus'.format(known_args.corpus_home)
    corpus_index = '{}/collections.csv'.format(corpus_data_dir)
    corpus_dir = known_args.corpus_home
    if known_args.corpus_prefix:
      corpus_dir = '{}/{}'.format(known_args.corpus_home,
                                  known_args.corpus_prefix)
    lines = (p | 'read_top_index' >> ReadFromText(corpus_index)
              | 'split_top_index' >> beam.ParDo(ExtractIndexEntry())
              | 'add_prefix_corpus_data' >> beam.FlatMap(add_prefix,
                                                         corpus_data_dir)
              | 'read_secondary_index' >> ReadAllFromText()
              | 'split_secondary_index' >> beam.ParDo(ExtractIndexEntry())
              | 'add_prefix_corpus_dir' >> beam.FlatMap(add_prefix, corpus_dir)
              | 'read_files' >> ReadAllFromText())
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
            | 'split' >> (beam.ParDo(TermExtractingDoFn())
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
    files_count_filter = MetricsFilter().with_name('files')
    files_query_result = result.metrics().query(files_count_filter)
    if files_query_result['counters']:
      files_counter = files_query_result['counters'][0]
      logging.info('Total files: %d (including index files)',
                   files_counter.result)
    chars_count_filter = MetricsFilter().with_name('chars')
    query_result = result.metrics().query(chars_count_filter)
    if query_result['counters']:
      chars_counter = query_result['counters'][0]
      logging.info('Total chars: %d', chars_counter.result)


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
run()