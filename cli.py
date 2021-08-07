from subjapflash.subjapflash import *
from subjapflash.helper import merge_matching_strings, init_anki_deck

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

for dir_name in [SUB_DIR, DECK_DIR, IGNORE_DIR, MATCH_DIR]:
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)
            
# Import match list
match = get_match_list()

parser = argparse.ArgumentParser(description='Convert a japanese subtitle file to a list of the most common words from that file & export as Anki flash card deck.')
parser.add_argument('-s', '--sub', type=str, help='Subtitle path. If arg not used, will process all files in Subtitles dir')
parser.add_argument('-t', '--top', type=int, help='Get the top n most common words. Default 10.')
parser.add_argument('-k', '--kana', type=str, help='Include kana in Anki card Question. Default True.')
parser.add_argument('-l', '--max_lines', type=int, help='Maximum number of lines to add to Anki cards answer. Default 10')
parser.add_argument('-i', '--ignore', action='store_true', help='Exports any added words to the ignore list')
parser.add_argument('-m', '--merge', action='store_true', help='Create one merged deck for all files in Subtitles dir')
parser.add_argument('-skip', '--skip_match', action='store_true', help='Dont filter out words in MATCH_LIST dir')
parser.add_argument('-c', '--count', type=int, help='Add all words with counts > n.')

args = parser.parse_args()
include_kana = args.kana == 'True' or args.kana == '1' if args.kana != None else INCLUDE_KANA
n_most_common = args.top if args.top else N_MOST_COMMON_WORDS
max_lines = args.max_lines if args.max_lines != None else MAX_ANSWER_LINE_COUNT
process_all = args.sub == None

if process_all:
    sub_files = [os.path.join(SUB_DIR, f) for f in os.listdir(SUB_DIR) if f.endswith('|'.join(valid_extensions))]
    if args.merge:
        merged_deck_name = merge_matching_strings([ntpath.basename(f).split('.')[0] for f in sub_files])
else:
    sub_files = [args.sub]
sub_files = sorted(sub_files)
    
for sub_idx, sub_file in enumerate(sub_files):
    if args.sub == None:
        deck_name = ntpath.basename(sub_file).split('.')[0]
        deck_name = merged_deck_name if args.merge and len(merged_deck_name) > 2 else deck_name
    else:
        default_name = DEFAULT_DECK_NAME.split('.')[0]
        deck_name = ntpath.basename(args.sub).split('.')[0] if args.sub != None else f'{default_name}_{sub_idx}'
    
    """
    Part 1: Get n most common Words --------------
    """
    # Get words to ignore from ignore directory
    ignore = dir_text_to_line_list(IGNORE_DIR)
    
    # Import subtitle text and parse in to word list using NLP package for tokenization
    word_counts = get_word_counts(sub_file, ignore, match, include_kana=include_kana, skip_match=args.skip_match, min_word_cnt=args.count)

    """
    Part 2: Get definitions & export to Anki Deck --------------
    """
    
    #Process each iteration in to a separate deck unless merge is True, then only create deck on first pass
    if sub_idx == 0 or not args.merge: 
        deck, template = init_anki_deck(deck_name)

    # Iterate most common words, get definition from jisho.org, add to anki card
    deck, words_added, skipped = build_deck_cards(word_counts, deck, template, n_most_common, max_lines=max_lines, min_word_cnt=args.count)

    # Export anki deck
    if not args.merge or sub_idx == len(sub_files)-1:
        genanki.Package(deck).write_to_file(f'{os.path.join(DECK_DIR, deck_name)}_Top{len(words_added)}.apkg')
    
    # Export List
    with open(os.path.join(DECK_DIR, deck_name+'.list'), 'w', encoding="utf-8") as file:
        file.writelines([w + '\n' for w in words_added])

    """
    Part 3: Export new ignore list to local ignore file --------------
    """
    new_ignore_words = skipped + words_added if args.ignore else skipped # Always add any skipped words, no need to ping jisho on these words in the future
    ignore_file = os.path.join(IGNORE_DIR, IGNORE_FILE_NAME)

    # Get existing text
    if os.path.isfile(ignore_file):
        for line in file_to_line_list(ignore_file):
            new_ignore_words += [line.replace('\n', '')]

        new_ignore_words = sorted(set(new_ignore_words))

    # Export new text
    with open(ignore_file, 'w', encoding="utf-8") as file:
        file.writelines([w + '\n' for w in new_ignore_words])
        
print()
print(f'Export complete. See {DECK_DIR}/ directory for exported anki decks.')
print(f'Please add any learned words to an ignore list in the {IGNORE_DIR}/ directory to filter from future decks.')
