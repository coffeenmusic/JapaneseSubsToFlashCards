import fugashi
from fugashi import Tagger

import genanki
import jisho
from urllib.parse import quote  

import argparse
import os
from collections import Counter, namedtuple
import random
import ntpath
        

# defaults
N_MOST_COMMON_WORDS = 10 # Top n most common words
MAX_ANSWER_LINE_COUNT = 100 # Number of lines allowed on Anki card's answer
DEFAULT_DECK_NAME = 'exported.apkg'
IGNORE_FILE_NAME = 'previous_export_words.txt'
SUB_DIR = 'Subtitles'
DECK_DIR = 'Anki_Decks'
IGNORE_DIR = 'Ignore_Lists'
MATCH_DIR = 'Match_Lists'
valid_extensions = ['.srt']

# class SubJapFlash():
    # def __init__(self, sub_dir, top=10):
        # self.sub_dir = sub_dir
        # self.sub_files = [os.path.join(SUB_DIR, f) for f in os.listdir(SUB_DIR) if f.endswith('|'.join(valid_extensions))]
        # self.sub_dict = {sub_file: self._get_word_counts(sub_file, top=top) for sub_file in self.sub_files}
        
    # def build_deck(self, sub_file, top=10):
        # #Process each iteration in to a separate deck unless merge is True, then only create deck on first pass
        # if sub_idx == 0 or not args.merge: 
            # deck, template = init_anki_deck(deck_name)
        # deck, words_added, skipped = build_deck_cards(word_counts, deck, template, n_most_common, max_lines=max_lines, min_word_cnt=args.count)
        
    # def _get_word_counts(self, sub_file, top=10, ignore_list=None, match_list=None, include_kana=True, skip_match=False, min_word_count=None):
        # if ignore_list == None:
            # ignore = dir_text_to_line_list(IGNORE_DIR)
        # if not skip_match and match_list == None:
            # match = get_match_list()
            
        # return get_word_counts(sub_file, ignore, match, include_kana=include_kana, skip_match=skip_match, min_word_cnt=min_word_count)
        
    # def __len__(self):
        # return len(os.listdir(sub_dir))

tagger = Tagger()

def file_to_line_list(filename, encoding='utf-8'):
    line_list = []
    with open(filename, 'r', encoding=encoding) as file:
            for line in file:
                line_list += [line.replace('\n', '')]
    return line_list

def dir_text_to_line_list(directory, ext='.txt'):
    line_list = []
    for dir_file in [f for f in os.listdir(directory) if f.endswith(ext)]:
        line_list += file_to_line_list(os.path.join(directory, dir_file))
    return line_list
    
def get_match_list():
    match = []
    for match_file in [f for f in os.listdir(MATCH_DIR) if f.endswith('.txt')]:
        for line in file_to_line_list(os.path.join(MATCH_DIR, match_file)):
            for word in line.replace(',', '\n').split('\n'):
                for token in tagger(word):
                    match += [token.surface]
    return match

def add_example(ex_dict, word, example, max_len=10):
    example_list = ex_dict.setdefault(word, [])
    if len(example_list) < max_len and example not in example_list:
        ex_dict[word] += [example]
        
def chunk_sub_idx_to_list(sub_line_list):
    """
        Pass in a list where each line is a line in the subtitle file
        Example:
        ['1', '00:00:00,000 --> 00:00:04,430', 'おはようございます', '2', ...]
        
        return a list where each list item is another list where each item is specific to its index
        Example:
        [['1', '00:00:00,000 --> 00:00:04,430', 'おはようございます'], ['2', ...], ...]
    """
    lines_indexed = []
    tmp = []
    for i, line in enumerate(sub_line_list):
        if line == '':
            continue

        tmp += [line]
        if len(tmp) > 3:
            digit, timestamp = tmp[-2:]
            if digit.strip().isdigit() and '-->' in timestamp:
                lines_indexed += [tmp[:-2]]
                tmp = tmp[-2:]
    return lines_indexed

def filter_lemma(text):
    return ''.join([c for c in text if c not in 'abcdefghijklmnopqrstuvwxyz-'])

Sub = namedtuple('SubtitleLineInfo', ('index', 'time', 'line', 'word', 'lemma', 'kana'))

def get_word_tuples(path):
    """
        Returns a list of namedtuples ('index', 'time', 'line', 'word', 'lemma', 'kana')
        for each index in the subtitle file
    """
    lines_indexed = chunk_sub_idx_to_list(file_to_line_list(path))
    
    word_tuples = []
    for idx in lines_indexed:
        if len(idx) <= 2:
            continue

        line_idx, timestamp = idx[:2]
        for line in idx[2:]:
            for word in tagger(line):
                if word.is_unk:
                    continue

                sub = Sub(line_idx, timestamp, line.strip(), word.surface, filter_lemma(word.feature.lemma), word.feature.kana)    
                word_tuples += [sub]    
    return word_tuples

def get_word_counts(word_tuples, ignore_list, match_list, skip_match=False, min_word_cnt=None):
    
    # Filter out ignore list words
    filtered = [w for w in word_tuples if w.word not in ['　', ' '] and w.word not in ignore_list and w.lemma not in ignore_list and not w.word.isdigit()]
    if not skip_match:
        filtered = [w for w in filtered if w.word in match_list or w.lemma in match_list]

    word_counts = Counter([(w.word, w.lemma) for w in filtered])
    
    # if min_word_cnt is used only keeps words where count > n 
    if min_word_cnt != None and min_word_cnt >= 0:
        for k, v in list(word_counts.items()):
            if v <= min_word_cnt:
                del word_counts[k]
                
    return word_counts

def get_word_counts2(sub_file, ignore_list, match_list, example_dict=None, include_kana=True, skip_match=False, min_word_cnt=None):
    all_words = []
    for line in file_to_line_list(sub_file):
        # Skip timestamp & index lines
        if '-->' in line or line.strip().isdigit():
            continue
                
        for word in tagger(line):
            if word.is_unk:
                continue
            
            kana_str = ''
            if include_kana and word.feature.kana:
                kana_str = ' ('+word.feature.kana+')'
            all_words += [word.surface+kana_str]
            
            # Save example
            example_dict = {} if example_dict == None else example_dict
            add_example(example_dict, word.surface+kana_str, line)
            

    # Filter out ignore list words
    filtered = [w for w in all_words if w not in ['　', ' '] and w.split()[0] not in ignore_list and not w.isdigit()]
    if not skip_match:
        filtered = [w for w in filtered if w.split()[0] in match_list]

    word_counts = Counter(filtered)
    
    # if min_word_cnt is used only keeps words where count > n 
    if min_word_cnt != None and min_word_cnt >= 0:
        for k, v in list(word_counts.items()):
            if v <= min_word_cnt:
                del word_counts[k]
                
    return word_counts
    
def build_deck_cards(word_counts, word_tuples, deck, template, n_most_common, furigana=True, include_stem=True, max_lines=100, min_word_cnt=None):
    words_added = []
    skipped = []
    for (word, lemma), _ in word_counts.most_common():
        kana = Counter([w.kana for w in word_tuples if (w.word, w.lemma) == (word, lemma)]).most_common()[0][0]
        search = lemma if lemma != None and lemma != '' else word

        unk_word = False
        try:
            answers = jisho.search(quote(search))
            if type(answers) != list:
                unk_word = True
            else:
                words_added += [word]
        except:
            unk_word = True            

        if unk_word:
            skipped += [search]
            print(f'Could not find definition for {word}. Skipping...')
            continue

        question = f'{word}[{kana}]'
        stem = 'Stem: '+lemma if include_stem and lemma != word else ''
            
        # Add Question & Answer to card
        card = genanki.Note(model=template, fields=[question, stem, parse_answer(answers), parse_example(word, lemma, word_tuples)])
        deck.add_note(card)

        if min_word_cnt == None and len(words_added) >= n_most_common:
            break
            
    return deck, words_added, skipped
    
def parse_answer(answers, max_lines=100):
    answer_str = ''
    line_cnt = 0
    for def_idx in range(len(answers)):
        def_en = answers[def_idx].en
        def_jp = answers[def_idx].ja

        # Add new line item for each definition
        answer_str += f'{def_idx+1}. {def_jp[0].word} ({def_jp[0].reading})<br>'
        line_cnt += 1

        # Build bullet list for each example under definition
        answer_str += '<ul>'
        for i, (en, jp) in enumerate(zip(def_en, def_jp)):
            jp_str = ' '.join(jp.reading)
            en_str = '; '.join(en.meaning)

            answer_str += '<li>'
            answer_str += f'({jp_str}) {en_str}' if len(answers[0].en) > 1 else f'({jp_str}) {en_str}'
            answer_str += '</li>'
            line_cnt += 1

            if line_cnt >= max_lines-1:
                break
        answer_str += '</ul>'

        if line_cnt >= max_lines-1:
            break
    return answer_str

def parse_example(word, lemma, word_tuples, max_lines=20):
    example_list = set([w.line for w in word_tuples if (w.word, w.lemma) == (word, lemma)])
    if example_list == None or len(example_list) == 0:
        return ''

    example_str = 'Examples: <br>'
    example_str += '<ul>'
    for i, example in enumerate(example_list):
        example_str += '<li>'
        example_str += example
        example_str += '</li>'
        if i > max_lines:
            break
    example_str += '</ul>'

    return example_str
