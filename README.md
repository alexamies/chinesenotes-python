# Chinese Notes Python Utilities
Python utilities for Chinese Notes Chinese-English dictionary

## Use the dictionary

From a directory above chinesenotes-python, clone the chinesenots.com project

```shell
git clone https://github.com/alexamies/chinesenotes.com.git
```

Set the location to an environment variable

```shell
export CNREADER_HOME=$HOME/chinesenotes.com
```

Lookup a word in the dictionary

```shell
python3 chinesenotes/cndict.py --lookup "你好"
```

You should see output like
```shell
INFO:root:Opening the Chinese Notes Reader dictionary
INFO:root:OpenDictionary completed with 141896 entries
INFO:root:hello
```

## Text Segmentation

Same as above for environment setup. To run the utility:

```shell
python3 chinesenotes/cndict.py --tokenize "東家人死。西家人助哀。"
```

You should see output like

```shell
INFO:root:Opening the Chinese Notes Reader dictionary
INFO:root:OpenDictionary completed with 141896 entries
INFO:root:Greedy dictionary-based text segmentation
INFO:root:Chunk: 東家人死。西家人助哀。
INFO:root:Segments: ['東家', '人', '死', '。', '西家', '人', '助', '哀', '。']
```

## Converting between simplified and traditionl

To convert traditional to simplified

```shell
python chinesenotes/charutil.py --tosimplified "四種廣說"
```

To convert to traditional

```shell
python chinesenotes/charutil.py --totraditional "操作系统"
```

To get pinyin

```shell
python chinesenotes/charutil.py --topinyin "操作系统"
```

## Text analysis

### Setup up
The text analysis programs require the Apache Beam Python SDK.
See 
[Apache Beam Python SDK Quickstart](https://beam.apache.org/get-started/quickstart-py/)
for details on running Apache Beam . You can run it locally or on the cloud 
Google Cloud Dataflow or another implementation.

A small corpus of Chinese texts is included in this repo. To run this on a full
corpus download either the Chinese Notes corpus of literary Chinese

```shell
git clone https://github.com/alexamies/chinesenotes.com.git
```

or the NTI Reader corpus for the Taisho Tripitaka version of the Chinese
Buddhist canon

```shell
git clone https://github.com/alexamies/buddhist-dictionary.git
```

Set environment variables

```shell
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
INPUT_BUCKET=ntinreader-text
OUTPUT_BUCKET=ntinreader-analysis
PROJECT=[your project]
```

Activate a virtual environment

```shell
python3 -m venv venv
source venv/bin/activate
```

### Character frequency analysis

To list all options

```shell
python charcount.py --help
```

To run locally, reading one file only

```shell
CORPUS_HOME=.
python charcount.py \
  --input $CORPUS_HOME/corpus/shijing/shijing001.txt \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output outputs
```

To process all files in corpus

```shell
CORPUS_HOME=.
python charcount.py \
  --corpus_home $CORPUS_HOME \
  --corpus_prefix corpus \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output outputs
```  

Run with Dataflow. You will need to copy the corpus text files into GCS first.
For a single file

```shell
python charcount.py \
  --input gs://$INPUT_BUCKET/taisho/t2003_01.txt \
  --output gs://$OUTPUT_BUCKET/analysis/outputs \
  --runner DataflowRunner \
  --project $PROJECT \
  --temp_location gs://$OUTPUT_BUCKET/tmp/
```  

Results

```shell
gsutil cat "gs://$OUTPUT_BUCKET/analysis/outputs*" > output.txt
less output.txt
rm output.txt
```

For the whole corpus, running on Dataflow

```shell
python charcount.py \
  --corpus_home gs://$INPUT_BUCKET \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output gs://$OUTPUT_BUCKET/charcount/outputs \
  --runner DataflowRunner \
  --project $PROJECT \
  --temp_location gs://$OUTPUT_BUCKET/tmp/
```  

Get the results

```shell
mkdir tmp
gsutil -m cp gs://$OUTPUT_BUCKET/analysis/* tmp/
cat tmp/* > char_freq.tsv
rm -rf tmp
```

### Term frequency analysis

To list all options

```shell
python term_frequency.py --help
```

Run locally, read one file only

```shell
CORPUS_HOME=.
python term_frequency.py \
  --input $CORPUS_HOME/corpus/shijing/shijing001.txt \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output outputs
```

Run on an entire corpus, locally

```shell
python term_frequency.py \
  --corpus_home $CORPUS_HOME \
  --corpus_prefix corpus \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --setup_file ./setup.py \
  --output outputs
```

Run on an entire corpus, using Dataflow

```shell
python term_frequency.py \
  --corpus_home gs://$INPUT_BUCKET \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output gs://$OUTPUT_BUCKET/termfreq/outputs \
  --runner DataflowRunner \
  --project $PROJECT \
  --setup_file ./setup.py \
  --temp_location gs://$OUTPUT_BUCKET/tmp/
```

Get the results

```shell
mkdir tmp
gsutil -m cp gs://$OUTPUT_BUCKET/analysis/* tmp/
cat tmp/* > term_freq.tsv
rm -rf tmp
```
