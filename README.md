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
The text analysis programs require the Apache Beam Python SDK. See 
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

Create a virtual environment

```shell
python3 -m venv venv
source venv/bin/activate
```

Install software and activate again when coming back.

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

To compute the character count for all files in corpus

```shell
CORPUS_HOME=.
python charcount.py \
  --corpus_home $CORPUS_HOME \
  --corpus_prefix corpus \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output outputs
```

Move the results to a convenient location

```shell
cat output* > data/corpus/analysis/char_freq.tsv 
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

### Character bigram frequency analysis

The command line options are the same as the charcount.py program.
To run locally, reading one file only

```shell
CORPUS_HOME=.
python char_bigram_count.py \
  --input $CORPUS_HOME/corpus/shijing/shijing001.txt \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output outputs
```

For the whole corpus

```shell
python char_bigram_count.py \
  --corpus_home $CORPUS_HOME \
  --corpus_prefix corpus \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output outputs
```  

Move the results to a convenient location

```shell
cat output* > data/corpus/analysis/char_bigram_freq.tsv 
```

Run on Dataflow

```shell
python char_bigram_count.py \
  --corpus_home gs://$INPUT_BUCKET \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output gs://$OUTPUT_BUCKET/charbigramcount/outputs \
  --runner DataflowRunner \
  --project $PROJECT \
  --temp_location gs://$OUTPUT_BUCKET/tmp/
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

For example, Blue Cliff Record Scroll 1:

```shell
CORPUS_HOME=../buddhist-dictionary
python term_frequency.py \
  --input $CORPUS_HOME/corpus/taisho/t2003_01.txt \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output output/bluecliff01.tsv
```

Run on the entire test corpus

```shell
python term_frequency.py \
  --corpus_home $CORPUS_HOME \
  --corpus_prefix corpus \
  --ignorelines $CORPUS_HOME/data/corpus/ignorelines.txt \
  --output outputs
```

Move the results to a convenient location

```shell
cat output* > data/corpus/analysis/term_freq.tsv 
```

Run using Dataflow

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

### Mutual Information
To compute the mutual information for each term and write it to an output file:

```shell
python chinesenotes/mutualinfo.py \
  --char_freq_file [FILE_NAME] \
  --bigram_freq_file [FILE_NAME] \
  --filter_file [FILE_NAME] \
  --output_file [FILE_NAME]
```

For example, for the test corpus

```shell
CORPUS_HOME=.
python chinesenotes/mutualinfo.py \
  --char_freq_file $CORPUS_HOME/data/corpus/analysis/char_freq.tsv \
  --bigram_freq_file $CORPUS_HOME/data/corpus/analysis/char_bigram_freq.tsv \
  --filter_file $CORPUS_HOME/data/corpus/analysis/term_freq.tsv \
  --output_file $CORPUS_HOME/data/corpus/analysis/mutual_info.tsv
```

For the NTI Reader Taisho corpus

```shell
CORPUS_HOME=../buddhist-dictionary
python chinesenotes/mutualinfo.py \
  --char_freq_file $CORPUS_HOME/index/char_freq.tsv \
  --bigram_freq_file $CORPUS_HOME/index/char_bigram_freq.tsv \
  --filter_file $CORPUS_HOME/index/term_freq.tsv \
  --output_file $CORPUS_HOME/index/mutual_info.tsv
```

Filter to specific terms, for example, the terms in the Blue Cliff Record,
Scroll 1:

```shell
CORPUS_HOME=../buddhist-dictionary
python chinesenotes/mutualinfo.py \
  --char_freq_file $CORPUS_HOME/index/char_freq.tsv \
  --bigram_freq_file $CORPUS_HOME/index/char_bigram_freq.tsv \
  --filter_file output/bluecliff01.tsv \
  --output_file output/bluecliff01_mi.tsv
```

Check for the term 蠛蠓 'midge' in the NTI Reader corpus:

Bigram freq (蠛蠓 + 蠓蠛): 13 + 1 = 14
Character freq (蠛): 19
Character freq (蠓): 23
Total characters: 85,519,494
Total bigrams: 83,666,199
Mutual information:
I(之,下) = log2[ P(a, b) / P(a) P(b)]
        = log2[(14 / 83666199) / [(19 / 85519494) * (23/85519494)]]
        = log2(2800443.4)
        = 21.42

which matches the output of the program.

### Process Annotated Corpus file

To process an annotated corpus file

```shell
python chinesenotes/process_annotated.py \
  --filename corpus/shijing/shijing_annotated_example.md \
  --mutual_info data/corpus/analysis/mutual_info.tsv \
  --outfile data/corpus/analysis/shijing_training_example.tsv
```

A tab separated output file will be written containing all the terms in the
annotated corpus and whether they were tokenized correctly.

To run with the NTI Reader *Blue Cliff Record* data set

```shell
export CORPUS_HOME=../buddhist-dictionary
python chinesenotes/process_annotated.py \
  --filename $CORPUS_HOME/data/corpus/analysis/tokenization_annotated.md \
  --mutual_info $CORPUS_HOME/index/mutual_info.tsv \
  --outfile $CORPUS_HOME/data/corpus/analysis/tokenization_training.tsv
```

### Plot Results of Tokenization

First [Install Matplotlib](https://matplotlib.org/users/installing.html).
Also, a graphics backend. For example, on Debian

```shell
sudo apt-get install python3-tk
```

To plot the result of processing the annotated corpus file

```shell
python chinesenotes/plot_tokenization_results.py \
  --infile data/corpus/analysis/shijing_training_example.tsv \
  --outfile data/corpus/analysis/shijing_training_example.png
```

For the *Blue Cliff Record*

```shell
python chinesenotes/plot_tokenization_results.py \
  --infile $CORPUS_HOME/data/corpus/analysis/tokenization_training.tsv \
  --outfile $CORPUS_HOME/data/corpus/analysis/tokenization_training.png
```

### Training the tokenizer
Dictionary tokenization is still used by a filter is training to qualify
whether to accept the token. The scikit-learn
[decision tree classifier](https://scikit-learn.org/stable/modules/tree.html)
is used for this.

Install 
[scikit-learn](https://scikit-learn.org/stable/install.html)

```shell
pip install -U scikit-learn
```

Run the trainer to the example corpus

```shell
python chinesenotes/train_tokenizer.py \
  --infile data/corpus/analysis/shijing_training_example.tsv \
  --outfile data/corpus/analysis/shijing_training_example.dot
```


For the *Blue Cliff Record*

```shell
python chinesenotes/train_tokenizer.py \
  --infile $CORPUS_HOME/data/corpus/analysis/tokenization_training.tsv
```

Also, the points with low mutual information may also be added before training.

Write output using graphviz

```shell
dot -Tps data/corpus/analysis/shijing_training_example.dot -o \
  data/corpus/analysis/shijing_training_example.ps
```