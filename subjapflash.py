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

# defaults
N_MOST_COMMON_WORDS = 10 # Top n most common words
MAX_ANSWER_LINE_COUNT = 10 # Number of lines allowed on Anki card's answer
INCLUDE_KANA = True # Include on Anki card's Question next to Kanji
IGNORE_ADDED = True
DEFAULT_DECK_NAME = 'exported.apkg'
IGNORE_FILENAME = 'previous_export_words.txt'
SUB_DIR = 'Subtitles'
DECK_DIR = 'Anki_Decks'
IGNORE_DIR = 'Ignore_Lists'
valid_extensions = ['.srt']

parser = argparse.ArgumentParser(description='Convert a japanese subtitle file to a list of the most common words from that file & export as Anki flash card deck.')
parser.add_argument('-s', '--sub', type=str, help='Subtitle path. If arg not used, will process all files in Subtitles dir')
parser.add_argument('-t', '--top', type=int, help='Get the top n most common words. Default 10.')
parser.add_argument('-k', '--kana', type=str, help='Include kana in Anki card Question. Default True.')
parser.add_argument('-l', '--max_lines', type=int, help='Maximum number of lines to add to Anki cards answer. Default 10')
parser.add_argument('-n', '--deck_name', type=str, help='What to name the exported deck')
parser.add_argument('-i', '--ignore_added', type=bool, help='Exports any added words to the ignore list. Default True')
parser.add_argument('-list', '--export_list', action='store_true', help='Exports any added words to the ignore list')

args = parser.parse_args()
include_kana = args.kana == 'True' or args.kana == '1' if args.kana != None else INCLUDE_KANA
n_most_common = args.top if args.top else N_MOST_COMMON_WORDS
export_list = args.export_list if args.export_list != None else False
max_lines = args.max_lines if args.max_lines != None else MAX_ANSWER_LINE_COUNT
process_all = args.sub == None

if process_all:
    sub_files = [os.path.join(SUB_DIR, f) for f in os.listdir(SUB_DIR) if f.endswith('|'.join(valid_extensions))]
else:
    sub_files = [args.sub]
    
for sub_idx, sub_file in enumerate(sub_files):
    if len(sub_files) > 1:
        deck_name = ntpath.basename(sub_file).split('.')[0]
    else:
        default_name = DEFAULT_DECK_NAME.split('.')[0]
        deck_name = args.deck_name if args.deck_name != None else f'{default_name}_{sub_idx}'
    
    """
    Part 1: Get n most common Words --------------
    """

    tagger = Tagger()
    for dir_name in [SUB_DIR, DECK_DIR, IGNORE_DIR]:
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)

    ignore = []
    for ignore_file in os.listdir(IGNORE_DIR):
        ignore_file = os.path.join(IGNORE_DIR, ignore_file)
        with open(ignore_file, 'r') as file:
            for line in file:
                ignore += [line.replace('\n', '')]

    #sub_extensions = ['srt']
    #sub_files = [f for f in os.listdir(SUB_DIR) if f.split('.')[-1] in sub_extensions]

    all_words = []
    with open(sub_file, 'r') as file:
        for line in file:
            for word in tagger(line):
                kana_str = ''
                if include_kana and word.feature.kana:
                    kana_str = ' ('+word.feature.kana+')'
                all_words += [word.surface+kana_str]

    filtered = [w for w in all_words if w.split()[0] not in ignore and not w.isdigit()]
    print(f'Total Words: {len(all_words)}, Filtered Words: {len(filtered)}')

    word_counts = Counter(filtered)
    print(word_counts.most_common()[:n_most_common])

    if export_list:
        with open(deck_name+'.list', 'w') as file:
            file.writelines([w[0]+'\n' for w in word_counts.most_common()[:n_most_common]])
        exit(0)



    """
    Part 2: Get definitions & export to Anki Deck --------------
    """


    model_id = random.randrange(1 << 30, 1 << 31)

    # Build template for card format
    template = genanki.Model(
      model_id,
      'Simple Model',
      fields=[
        {'name': 'Question'},
        {'name': 'Answer'},
      ],
      templates=[
        {
          'name': 'Card 1',
          'qfmt': '{{Question}}',
          'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
        },
      ])

    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(
      deck_id,
      deck_name)

    def parse_answer(answers):
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
                en_str = ' '.join(en.meaning)

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

    add_cnt = 0
    words_added = []
    for word, _ in word_counts.most_common():
        word_no_kana = word.split()[0] # Ignore kana. Get just 俺 instead of 俺 (オレ)

        unk_word = False
        try:
            answers = jisho.search(quote(word_no_kana))
            if type(answers) != list:
                unk_word = True
            words_added += [word_no_kana]
        except:
            unk_word = True

        if unk_word:
            print(f'Could not find definition for {word}. Skipping...')
            continue

        # Add Question & Answer to card
        card = genanki.Note(model=template, fields=[word, parse_answer(answers)])
        deck.add_note(card)

        add_cnt += 1

        if add_cnt >= n_most_common:
            break

    # Export anki deck
    genanki.Package(deck).write_to_file(f'{os.path.join(DECK_DIR, deck_name)}_Top{n_most_common}.apkg')

    IGNORE_FILENAME = 'previous_export_words.txt'
    ignore_file = os.path.join(IGNORE_DIR, IGNORE_FILENAME)

    if os.path.isfile(ignore_file):
        with open(ignore_file, 'r') as file:
            for line in file:
                words_added += [line.replace('\n', '')]

    words_added = sorted(set(words_added))

    with open(ignore_file, 'w') as file:
        file.writelines([w + '\n' for w in words_added])

