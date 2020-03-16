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

"""Loads configuration settings

Uses the environment variable CNREADER_HOME to find the dictionary home
"""

import os

class ConfigException(Exception):
  """An app configuration problem"""


class AppConfig:
  """Loads the app config settings"""

  def __init__(self):
    """Constructor"""
    self._lex_unit_files = []

  @property
  def lex_unit_files(self):
    """A list of lexical unit files containing dictionary terms"""
    return self._lex_unit_files


  def load(self):
    """Loads configuraiton settings

    Raises:
      ConfigException: if there is a problem
    """
    if 'CNREADER_HOME' not in os.environ:
      raise ConfigException('Please define CNREADER_HOME')
    cn_home = os.environ['CNREADER_HOME']
    fname = f'{cn_home}/config.yaml'
    with open(fname, 'r') as config_file:
      for line in config_file:
        if 'LUFiles' in line:
          value = line.split(':')[1]
          value = value.strip()
          fnames = value.split(',')
          for fname in fnames:
            self._lex_unit_files.append(f'{cn_home}/data/{fname}')
