from subjapflash import SubJapFlash
from helper import merge_matching_strings, init_anki_deck

import fugashi
from fugashi import Tagger

import genanki
import jisho
from urllib.parse import quote  

import argparse
import os
from collections import Counter
import random
import ntpath

SUB_DIR = 'Subtitles'
IGNORE_DIR = 'Ignore_Lists'
MATCH_DIR = 'Match_Lists'
DECK_DIR = 'Anki_Decks'
N_MOST_COMMON_WORDS = 10 # Top n most common words
MAX_ANSWER_LINE_COUNT = 100 # Number of lines allowed on Anki card's answer

for dir_name in [SUB_DIR, DECK_DIR, IGNORE_DIR, MATCH_DIR]:
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)

parser = argparse.ArgumentParser(description='Convert a japanese subtitle file to a list of the most common words from that file & export as Anki flash card deck.')
parser.add_argument('-s', '--sub', type=str, help='Subtitle directory. If arg not used, will process all files in Subtitles dir')
parser.add_argument('-t', '--top', type=int, help='Get the top n most common words. Default 10.')
parser.add_argument('-n', '--no_furigana', action='store_true', help='Remove furigana from anki cards question')
parser.add_argument('-l', '--max_lines', type=int, help='Maximum number of lines to add to Anki cards answer. Default 100')
parser.add_argument('-i', '--ignore', action='store_true', help='Exports any added words to the ignore list')
parser.add_argument('-m', '--split', action='store_true', help='Final deck will contain top_n*number_subtitle_files')
parser.add_argument('-skip', '--skip_match', action='store_true', help='Dont filter out words in MATCH_LIST dir')
parser.add_argument('-c', '--count', type=int, help='Add all words with counts > n.')

args = parser.parse_args()
n_most_common = args.top if args.top else N_MOST_COMMON_WORDS
max_lines = args.max_lines if args.max_lines != None else MAX_ANSWER_LINE_COUNT
min_word_cnt = args.count if args.count != None else None
process_all = args.sub == None

sub_dir = args.sub if args.sub else SUB_DIR
filter_match = False if args.skip_match else True
furigana = False if args.no_furigana else True
per_file = True if args.split else False
export_ignore = True if args.ignore else False

sub = SubJapFlash(sub_dir, IGNORE_DIR, filter_match=filter_match)
sub.build_deck(n_most_common, furigana=furigana, per_file=per_file, max_example_lines=max_lines, min_word_cnt=min_word_cnt)
sub.export(export_dir=DECK_DIR, words_to_ignore_list=export_ignore)
        
print()
print(f'Export complete. See {DECK_DIR}/ directory for exported anki decks.')
print(f'Please add any learned words to an ignore list in the {IGNORE_DIR}/ directory to filter from future decks.')
