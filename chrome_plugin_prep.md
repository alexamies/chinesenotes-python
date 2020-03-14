# Building the Zhongzhong Chrome Plug-in for Chinese Notes

In development and not working yet

These are instruction to add the Chinese Notes dictionary to the 
[Zhongzhong Chrome plugin](https://github.com/PabloRomanH/zhongzhong)

Some of the details of the Chinese Notes dictionary may be lost, like part of
speech, notes, and word sense is mixed up with multiple equivalents.

The plug-in is based on the CC-CEDICT Chinese-English dictionary and assumes the
name of the dictionary file is cedict_ts.u8:

https://github.com/PabloRomanH/zhongzhong/blob/master/dict.js#L108

The instructions here show how to replace that with the Chinese Notes dicitonary
and update the index.

## Setup

Prerequesities: 
1. Python 3
2. Git

Instructions here assume Linux or Mac.

Starting from a top level directory, above this repo, clone the Chinese Notes or
NTI Reader repo, which contains the same dictionary

```shell
git clone https://github.com/alexamies/buddhist-dictionary.git
```

Export an environment variable to let the Python script know where to find it

```shell
export CNREADER_HOME=$PWD/buddhist-dictionary
```

Clone the Zhongzhong repo

```shell
git clone https://github.com/PabloRomanH/zhongzhong.git
```

Clone this repo and change directories into it

```shell
git clone https://github.com/alexamies/chinesenotes-python.git
cd chinesenotes-python
```

## Generate the dictionary file in CC-CEDICT format

```shell
python3 -m chinesenotes.cndict --convert ~/src/zhongzhong/data/cedict_ts.u8
```

Load the browser plugin in unpacked mode to test.