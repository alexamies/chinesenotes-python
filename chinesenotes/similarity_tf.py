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
Trains a decision tree classifier for phrase similarity.

Reads the input file and trains the classifier.
"""

import argparse
import logging
import numpy as np
import pandas as pd
import pathlib
from sklearn.metrics import confusion_matrix
import tensorflow as tf
from tensorflow import feature_column
from tensorflow import keras
from tensorflow.keras import layers


TRAIN_FILE_DEF = 'data/training_combined.csv'
VALIDATION_FILE_DEF = 'data/validation_biyan.csv'


def run(train_file: str, val_file: str):
  """Load training and validation data and train the classifier

  Args:
    train_file: input file with phrase similarity training data
    val_file: input file with phrase similarity training data
  """
  logging.info(f'Training data from: {train_file}')
  train_df = pd.read_csv(train_file)
  logging.info(f'Validation data from: {val_file}')
  val_df = pd.read_csv(val_file)
  print(train_df.head(3))
  train_data = pd.DataFrame({
    'QueryLength': train_df['Query'].str.len(),
    'UnigramCount': train_df['Unigram Count'],
    'Hamming': train_df['Hamming'],
    'Relevant': train_df['Is Relevant']
  })
  val_data = pd.DataFrame({
    'QueryLength': val_df['Query'].str.len(),
    'UnigramCount': val_df['Unigram Count'],
    'Hamming': val_df['Hamming'],
    'Relevant': val_df['Is Relevant']
  })
  logging.info('Sample prepared data')
  print(train_data.head(3))
  logging.info('Summary of traininging data')
  print(train_data.info())
  logging.info('Summary of validation data')
  print(train_data.info())
  train_ds = to_dataset(train_data)
  val_ds = to_dataset(val_data)
  feature_columns = []
  headers = ['QueryLength', 'UnigramCount', 'Hamming']
  for header in headers:
    feature_columns.append(feature_column.numeric_column(header))
  feature_layer = tf.keras.layers.DenseFeatures(feature_columns)
  model = tf.keras.Sequential([
    feature_layer,
    layers.Dense(128, activation='relu'),
    layers.Dense(128, activation='relu'),
    layers.Dropout(.1),
    layers.Dense(1)
  ])
  model.compile(optimizer='adam',
                loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
                metrics=['accuracy'])
  model.fit(train_ds,  validation_data=val_ds, epochs=10)
  #y_pred = model.predict(train_ds)
  #cm = confusion_matrix(headers, y_pred)
  #print(cm)


def to_dataset(df, batch_size=5):
  """Convert from Pandas dataframe to TensorFlow dataset. """
  df = df.copy()
  labels = df.pop('Relevant')
  ds = tf.data.Dataset.from_tensor_slices((dict(df), labels))
  ds = ds.batch(batch_size)
  return ds


def main():
  logging.basicConfig(level=logging.INFO)
  parser = argparse.ArgumentParser()
  parser.add_argument('--trainfile',
                      dest='trainfile',
                      default=TRAIN_FILE_DEF, 
                      help='File name to read training data from')
  parser.add_argument('--valfile',
                      dest='valfile',
                      default=VALIDATION_FILE_DEF, 
                      help='File name to read validation data from')
  args = parser.parse_args()
  logging.info(f'Training neural net classifier from {args.trainfile}, output to {args.valfile}')
  run(args.trainfile, args.valfile)


# Entry point from a script
if __name__ == "__main__":
  main()