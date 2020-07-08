# Chinese Notes Python Utilities
Python utilities for Chinese Notes Chinese-English dictionary

Prerequisite: Python 3.6+

Create a virtual environment

```shell
python3 -m venv venv
source venv/bin/activate
```

Install software and activate again when coming back.

## Basic dictionary and text utilities

You can use the chinesenotes Python package for basic command line utilities
as described here.

### Use the dictionary

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
python -m chinesenotes.cndict --lookup "你好"
```

You should see output like
```shell
INFO:root:Opening the Chinese Notes Reader dictionary
INFO:root:OpenDictionary completed with 141896 entries
INFO:root:hello
```

### Text Segmentation

Same as above for environment setup. To run the utility:

```shell
python -m chinesenotes.cndict --tokenize "東家人死。西家人助哀。"
```

You should see output like

```shell
INFO:root:Opening the Chinese Notes Reader dictionary
INFO:root:OpenDictionary completed with 141896 entries
INFO:root:Greedy dictionary-based text segmentation
INFO:root:Chunk: 東家人死。西家人助哀。
INFO:root:Segments: ['東家', '人', '死', '。', '西家', '人', '助', '哀', '。']
```

### Word Similarity

To run the word similarity tool

```shell
python -m chinesenotes.similarity  --word TARGET_WORD
```

Substitute the value of TARGET_WORD for your search.

### Converting between simplified and traditional

To convert traditional to simplified

```shell
python main.py --tosimplified "四種廣說"
```

To convert to traditional

```shell
python main.py --totraditional "操作系统"
```

To get pinyin

```shell
python main.py --topinyin "操作系统"
```

### Colab Notebook

The Colab notebook to add new words is at (open with Chrome)
http://colab.research.google.com/github/alexamies/chinesenotes-python/blob/master/add_mod_entry.ipynb

## Text analysis

### Setup up
The text analysis programs require the Apache Beam Python SDK. See 
[Apache Beam Python SDK Quickstart](https://beam.apache.org/get-started/quickstart-py/)
for details on running Apache Beam . You can run it locally or on the cloud 
Google Cloud Dataflow or another implementation.

```shell
pip install apache-beam
```

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
rm output*
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

Filter to specific terms, for example, the terms in the *Blue Cliff Record*,
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
  --outfile $CORPUS_HOME/data/corpus/analysis/tokenization_training.png \
  --decision_point -0.507
```

### Training the tokenizer
Dictionary tokenization is still used by a filter is training to qualify
whether to accept the token. The scikit-learn
[decision tree classifier](https://scikit-learn.org/stable/modules/tree.html)
is used for this.

Install 
[scikit-learn](https://scikit-learn.org/stable/install.html) and 
[graphviz](https://graphviz.gitlab.io/documentation/)

```shell
pip install -U scikit-learn
pip install graphviz
```

Run the trainer to the example corpus

```shell
python chinesenotes/train_tokenizer.py \
  --infile data/corpus/analysis/shijing_training_example.tsv \
  --outfile data/corpus/analysis/shijing_example_decision_tree.png
```


For the *Blue Cliff Record*

```shell
python chinesenotes/train_tokenizer.py \
  --infile $CORPUS_HOME/data/corpus/analysis/tokenization_training.tsv \
  --outfile $CORPUS_HOME/data/corpus/analysis/tokenization_decision_tree.svg
```

Also, the points with low mutual information can also be added before training.

## Testing

Run unit tests with the command
```shell
python -m unittest discover -s tests -p "*_test.py"
```

## Appendix A: Term segmentation analysis data
The format of the text below is:
Segmented Chinese text [English no. segments]
Legend: 
Error false positive (segmentation incorrectly predicted by the NTI Reader) 
Error: false positive (not in dictionary on first pass, or not detected)
English translation is followed by number of segments
Segments are delimited by Chinese enumeration mark 、

Source (English): Cleary, T 1998, *The Blue Cliff Record*, Berkeley: Numata Center for Buddhist Translation and Research, https://www.bdkamerica.org/book/blue-cliff-record. 
Source (Chinese): Chong Xian and Ke Qin, 《佛果圜悟禪師碧巖錄》 'The Blue Cliff Record (Biyanlu),' in *Taishō shinshū Daizōkyō* 《大正新脩大藏經》, in Takakusu Junjiro, ed., (Tokyo: Taishō Shinshū Daizōkyō Kankōkai, 1988), Vol. 48, No. 2003, accessed 2020-01-26, http://ntireader.org/taisho/t2003_01.html.  
Koan 1
Source: Cleary 1998, pp. 11-12

舉、梁武帝、問、 達磨、大師 
Story: The Emperor Wu of Liang asked the great teacher Bodhidharma 5
 (說、這、不、唧𠺕、漢) 
(Here’s someone talking such nonsense.) 5
如何、是、聖諦、第一義
“What is the ultimate meaning of the holy truths?” 4
 (是、甚、繫驢橛)
(What donkey-tethering stake is this?) 3
磨  云。
Bodhidharma said, 2
廓然無聖
“Empty, nothing holy.” 1
(將、謂、多少、奇特。
(One might have thought he’d say something extraordinary. 4
箭、過、新羅。
The point has already whizzed past. 3
可、殺、明白)
It’s quite clear.) 3
帝、曰。
The emperor said, 2
對、朕、者、誰
“Who is answering me?” 4
(滿面、慚惶。
(Filled with embarrassment, 2
強、惺惺  果然。
he tries to force himself to be astute. 3
摸索、不、着)
After all he gropes without finding.) 3
磨、云。
Bodhidharma said, 2
不識
“Don’t know.” 1
(咄。[(Tsk! 1] 再、來、不、直  半、文、錢)
A second try isn’t worth half a cent.) 7
帝、不、契
The emperor didn’t understand. 3
(可惜、許。
(Too bad. 2
却、較、些、子)
Still, this is getting somewhere.) 4
達磨、遂、渡江、至、魏( 
Bodhidharma subsequently crossed the Yangtse River into the kingdom of Wei. 5
(這、野狐精。
(Foxy devil! 2
不免、一、場、懡、㦬。
He can’t avoid embarrassment. 5
從、西、過、東。
He goes from west to east, 4
從、東、過、西) 
east to west.) 4

帝、後、舉、問、志、公
Later the emperor brought this up to Master Zhi and asked him about it. 6
(貧、兒、思、舊、債。
(A poor man remembers an old debt. 5
傍人、有、眼)
The bystander has eyes.) 3
志、公、云。
Master Zhi said, 3
陛下、還、識、此、人、否
“Did you recognize the man?” 6
(和、志、公、趕、出國、始、得。
(He should drive Master Zhi out of the country too. 7
好、與、三十、棒。
He deserves a beating. 4
達磨、來、也)
Bodhidharma is here.) 3
帝、云。
The emperor said 2
不識
he didn’t know him. 1
(却是、武帝、承當、得、達磨、公案)
(So after all the Emperor Wu has understood Bodhidharma’s case.) 6
志、公、云。
Master Zhi said, 3
此、是、觀音、大士。
“He is Mahasattva Avalokitesvara, 4
傳、佛心印 
transmitting the seal of the Buddha mind.” 2
(胡亂、指、注。
(An arbitrary explanation. 3
臂膊、不、向、外、曲) 
The elbow doesn’t bend outwards.) 5
帝、悔。
The emperor, regretful, 2
遂、遣使、去、請
sent an emissary to invite Bodhidharma back. 4
(果然、把、不住。
(After all Wu can’t hold Bodhidharma back; 3
向、道、不唧、𠺕)
I told you he was a dunce.) 4
志、公、云。
Master Zhi said, 3
莫道、陛下、發、使、去、取
“Don’t tell me you’re going to send an emissary to get him!” 6
(東家、人、死。
(When someone in the house to the east dies, 3
西家、人、助、哀。
someone from the house to the west helps in the mourning. 4
Error: 西家 (false negative, missing term)
也好、一時  趕、出國)
Better they should all be driven out of the country at once.) 4
闔、國人、去。
“Even if everyone in the country went, 4
他、亦、不、回
he wouldn’t return.” 4
(志、公、也好、與、三十、棒。
(Master Zhi again deserves a beating. 6
不知、脚跟、下放、大、光明)。
He doesn’t know the great illumination shines forth right where one is.) 5
Error: 下放 (false positive)

Note: total 199 segments, 2 errors (1 false negative, 1 false positive)

## Appendix B: Calculation of Character Bigram Correlation
### Pointwise Mutual Information
The probability p(a, b) can be computed as 

p(a, b)  = [f(ab) + f(ba)] / B

Where f(ab) is the frequency of the character bigram ab, f(ba) is the frequency of character bigram of ba and  B is the total number of character bigrams.

These should be computed over the entire corpus but let’s use Scroll 1 of the Blue Cliff Record for a simple illustration. It is preferable to compute the frequencies over the entire corpus (volumes 1-55 of the Taisho) for more representative statistical values than just the given document in question. 西家 occurs 53 times in the corpus and 家西 occurs 4 times. The corpus is 85,519,494 characters and 83,666,199 character bigrams. 西 occurs 30743 times and . The pointwise mutual information is 

p(西家) = (53 + 4) / 83666199 = 0.0000006665145
p(西) = 30743 / 83666199 = 0.000367448
p(家) = 66590 / 83666199 = 0.000795901
I(西, 家) = log2[0.0000006665145 / (0.000367448 * 0.000795901)] = log2(2.27905) = 1.19
T value
The t value for the character bigram 西家 is approximately,

x ~= P(西家) = 53 / 83666199 = 0.0000006334697
s2 ~= x
μ = P(西) · P(家) = 0.000367448 * 0.000795901 = 0.0000002924522
t = [x - μ] / [s2 / N]1/2 
  = [(0.0000006334697 - 0.0000002924522) / (0.0000006334697 / 85519494)1/2 
  =  3.96
Chi Square
For a 2-by-2 matrix, such as the test for bigram correlation, the chi-square statistic is given by the formula

X2 = N(O11O22 - O12O21) / [(O11 + O12)(O11 + O21)(O12 + O22)(O21 + O22)]

Where N is the total number of bigrams in the corpus and Oij are the values observed each combination of characters i and j. For example, for 西家

O11 = 53 (count for 西 followed by 家)
O12 = 30743 (count for 西 not followed by 家)
O21 = 66590 (count for not 西 followed by 家)
O22 = 85519494 - 66590 - 30743 = 85422161 (count for not 西 followed by not 家)
X2 = 85519494 * (53 * 85422161 - 30743 * 66590)2 / ((53 + 30743) * (53 + 66590) * (30743 + 85422161) * (66590 + 85422161))
  = 35.1
