# Chinese Notes Python Utilities
Python utilities for Chinese Notes Chinese-English dictionary

## Open the dictionary file

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
python3 cndict.py "你好"
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
python3 textsegmentation.py "東家人死。西家人助哀。"
```

You should see output like

```shell
INFO:root:Opening the Chinese Notes Reader dictionary
INFO:root:OpenDictionary completed with 141896 entries
INFO:root:Greedy dictionary-based text segmentation
INFO:root:Chunk: 東家人死。西家人助哀。
INFO:root:Segments: ['東家', '人', '死', '。', '西家', '人', '助', '哀', '。']
```

## Text analysis

See [Quickstart using Python](https://cloud.google.com/dataflow/docs/quickstarts/quickstart-python)

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

Run locally, read one file only

```shell
CORPUS_HOME=.
python charcount.py \
  --input $CORPUS_HOME/corpus/shijing/shijing001.txt \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output outputs
```

Process all files in corpus

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

For the whole corpus

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
gsutil cp gs://$OUTPUT_BUCKET/analysis/* tmp/
cat tmp/* > char_freq.tsv
rm -rf tmp
```