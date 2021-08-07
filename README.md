References:
- https://github.com/polm/fugashi#installing-a-dictionary
- https://github.com/kerrickstaley/genanki
- https://github.com/PokiDokika/jisho-py

Subtitle Sites:
- https://kitsunekko.net

# How it works
### Anki Flash Card Example

![Example](example.png)

Download a japanese subtitle file (place in Subtitles dir). This tool will parse that file and give you the n most common japanese words used (Words not in the Match_List dir will be filtered out). The words are translated using jisho.org as the dictionary. It will then export those words and translations to an Anki flash card deck for spaced repetition studying.
Any learned words should be added to an ignore list .txt file in the Ignore_Lists/ directory. Any words that return null results on jisho.org will be added to an ignore list.

# Dependencies
- fugashi - package for japanese language tokenization (I'm using it to break the corpus in to separate words)
- jisho-py - package creates a python api to jisho.org japanese dictionary and returns results with japanese kanji & kana as well as english translations
Note: jisho-py currently must be copied to the site-packages directory because it's pip installation is broken. Just import a package like import numpy as np, then `print(np.__file__)` to get the site-packages location
- genanki - package for generating anki decks

# Usage
- Export all subtitle files in Subtitles directory to anki decks (10 most common words default)
    ```
    python cli.py
    ```
- Export anki deck with 20 most common words and no kana for all subtitle files in Subtitles directory
    ```
    python cli.py --top 20 --kana False 
    ```
- Export all subtitle files in Subtitles directory to a single anki deck
    ```
    python cli.py --merge
    ```
- Allow words outside N5-N1 core dictionary (You can also add your own words to MATCH_LISTS dir)
    ```
    python cli.py --skip_match
    ```
    
### optional arguments:
```
  -s, --sub Subtitle path. If arg not used, will process all files in Subtitles dir
  -t, --top Get the top n most common words. Default 10.
  -k, --kana Include kana in Anki card Question. Default True.
  -l, --max_lines Maximum number of lines to add to Anki cards answer. Default 10
  -i, --ignore Exports any added words to the ignore list. Default True
  -m, --merge Exports all subtitle files' most common words to a single deck
  -skip, --skip_match Dont filter out words in MATCH_LIST dir
  -c, --count Get all words with count greater than --count n
``` 

Notes
- To automatically add exported words to an ignore list use `--ignore`.