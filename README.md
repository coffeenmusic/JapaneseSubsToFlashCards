References:
- https://github.com/polm/fugashi#installing-a-dictionary
- https://github.com/kerrickstaley/genanki
- https://github.com/PokiDokika/jisho-py

Subtitle Sites:
- https://kitsunekko.net

# How it works
### Anki Flash Card Example

![Example](example.png)

Download a japanese subtitle file. This tool will parse that file and give you the n most common japanese words used (Words not in the Match_List dir will be filtered out). The words are translated using jisho.org as the dictionary. It will then export those words and translations to an Anki flash card deck for spaced repetition studying.
Any words added to a deck will also be added to an ignore list in the IGNORE_LIST directory.

# Dependencies
- fugashi - package for japanese language tokenization (I'm using it to break the corpus in to separate words)
- jisho-py - package creates a python api to jisho.org japanese dictionary and returns results with japanese kanji & kana as well as english translations
Note: jisho-py currently must be copied to the site-packages directory because it's pip installation is broken. Just import a package like import numpy as np, then `print(np.__file__)` to get the site-packages location
- genanki - package for generating anki decks

# Usage
- Export anki deck with 10 most common words and kana included in question
    ```
    python subjapflash.py -s Subtitles/Naruto_Shippuuden_393.srt
    ```
- Export anki deck with 20 most common words and no kana
    ```
    python subjapflash.py -s Subtitles/Naruto_Shippuuden_393.srt --top 20 --kana False 
    ```
- Save with different deck name
    ```
    python subjapflash.py -s Subtitles/Naruto_Shippuuden_393.srt --deck_name My_Custom_Deck
    ```
- Export all subtitle files in Subtitles directory to anki decks (exclude -s arg)
    ```
    python subjapflash.py
    ```
- Export all subtitle files in Subtitles directory a single anki deck (exclude -s arg)
    ```
    python subjapflash.py --merge
    ```
- Allow words outside N5-N1 core dictionary (You can also add your own words to MATCH_LISTS dir)
    ```
    python subjapflash.py --skip_match
    ```
    
### optional arguments:
```
  -s, --sub Subtitle path. If arg not used, will process all files in Subtitles dir
  -t, --top Get the top n most common words. Default 10.
  -k, --kana Include kana in Anki card Question. Default True.
  -l, --max_lines Maximum number of lines to add to Anki cards answer. Default 10
  -n, --deck_name What to name the exported deck
  -i, --ignore_added Exports any added words to the ignore list. Default True
  -m, --merge Exports all subtitle files' most common words to a single deck
  -list, --export_list  Exports any added words to the ignore list
``` 

Notes
- All words will automatically be added to the ignore list under the `IGNORE_LIST/previous_export_words.txt` unless the `--ignore_added True` argument is used.
- The anki deck's card answer will be limited to how many lines are added with the `--max_lines` arg (default 10). The code will continue to iterate words and definitions on jisho.org until the max line count is reached.