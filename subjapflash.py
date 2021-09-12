import fugashi
from fugashi import Tagger

import genanki
import jisho
from urllib.parse import quote  

import pandas as pd
import argparse
import os
from collections import Counter, namedtuple
import random
import ntpath
        
pd.set_option('mode.chained_assignment', None)

# defaults
MATCH_DIR = 'Match_Lists'

class SubJapFlash():
    deck_style = """
    .card {
     font-size: 16px;
     text-align: left;
     color: black;
     background-color: white;
    }
    .stem {
     font-size: 32px;
     text-align: center;
    }
    .question {
     font-size: 64px;
     text-align: center;
    }
    """
    VALID_EXTENSIONS = ['.srt']
    IGNORE_FILE_NAME = 'previous_export_words.txt'
    _cols = ['file','line_idx','word','lemma','kana','time','line']
    _not_alpha = '｡,(,),～,♪,？,》,《,:,00,-->,\u3000,。,！,　,（,）,→,…,…｡,?,]（,[,],➡,･,・,．,!,ー,]（,Ｔ,Ｂ +,Ｂ,Ｃ,―],:,：,＜,→,/,＞'.split(',')  
    
    def __init__(self, sub_dir='Subtitles', ignore_dir='Ignore_Lists', filter_ignore=True, filter_match=True):
        """
        Parameters
        ----------
        sub_dir : str
            path of directory containing one or multiple subtitle files
        filter_ignore : bool
            remove any words in the ignore lists from the ignore directory
        """
        for path in [sub_dir, ignore_dir]:
            assert os.path.exists(path), f'Path provided does not exist. {path}'
            
        self.sub_dir = sub_dir
        self.ignore_dir = ignore_dir
        self.sub_files = sorted([os.path.join(sub_dir, f) for f in os.listdir(sub_dir) if f.endswith('|'.join(self.VALID_EXTENSIONS))])
        self.ignore_files = sorted([os.path.join(ignore_dir, f) for f in os.listdir(ignore_dir) if f.endswith('.txt')])
        self._tagger = Tagger()
        
        self.dataset = pd.concat([self._subfile_to_dataset(sub_file) for sub_file in self.sub_files])
        if filter_ignore:
            self.filter_ignore()
            
        if filter_match:
            self.filter_match()
            
        self._get_word_counts()
        
    def filter_ignore(self, ignore=None):
        self._import_ignore_lists()
        if ignore and type(ignore) == list:
            self.ignore += ignore
        
        df = self.dataset
        self.dataset = df.loc[~((df.word.isin(self.ignore)) | (df.lemma.isin(self.ignore)))].reset_index(drop=True)
        
    def filter_match(self, match=None):
        self._import_match_list()
        if match and type(match) == list:
            self.match += match
        
        df = self.dataset
        self.dataset = df.loc[(df.word.isin(self.match)) | (df.lemma.isin(self.match))].reset_index(drop=True)
        
    def build_deck(self, n_most_common, deck_name=None, furigana=True, per_file=False, max_example_lines=100, min_word_cnt=None):
        sub_name_list = [os.path.basename(f).split('.')[0] for f in set(self.dataset.file)]
        self.deck_name = deck_name if deck_name else self.__merge_matching_strings(sub_name_list)
        
        self.__init_anki_deck(self.deck_name, furigana)
        self._add_cards(n_most_common, max_lines=max_example_lines, min_word_cnt=min_word_cnt)
        
    def export(self, export_name=None, export_dir='Anki_Decks', export_deck=True, export_list=True, words_to_ignore_list=False):
        assert hasattr(self, 'deck'), 'Please run build_deck() before export.'
            
        deck_name = export_name if export_name else self.deck_name
        
        # Export anki deck
        if export_deck:
            genanki.Package(self.deck).write_to_file(f'{os.path.join(export_dir, deck_name)}_Top{len(self.words_added)}.apkg')

        # Export List
        if export_list:
            with open(os.path.join(export_dir, f'{deck_name}_Top{len(self.words_added)}.list'), 'w', encoding="utf-8") as file:
                file.writelines([w + '\n' for w in self.words_added])
        
        # Add skipped words to ignore list, optionally add new words to ignore list
        self._update_ignore_files(new=words_to_ignore_list)
                
    def _update_ignore_files(self, new=False, skipped=True):
        new_ignore_words = []
        if new:
            new_ignore_words += self.words_added
        if skipped:
            new_ignore_words += self.skipped
            
        ignore_file = os.path.join(self.ignore_dir, self.IGNORE_FILE_NAME)

        # Get existing text
        if os.path.isfile(ignore_file):
            for line in self._file_to_line_list(ignore_file):
                new_ignore_words += [line.replace('\n', '')]

            new_ignore_words = sorted(set(new_ignore_words))

        # Export new text
        with open(ignore_file, 'w', encoding="utf-8") as file:
            file.writelines([w + '\n' for w in new_ignore_words])
        
    def _add_cards(self, n_most_common, furigana=True, include_stem=True, max_lines=100, min_word_cnt=None, per_file=False, common_only=True):
        """
            Iterate through self.dataset and add all most_common words to Anki Deck.
            Parameters
            ----------
            per_file : bool
                n_most_common will be across all files by default. If True, n words will be collected for each subtitle file.
            common_only : bool
                words searched on on jisho return an iscommon parameter. If True, only common words are added.
        """
        
        words_added = []
        skipped = []
        
        cnt_col = 'file_cnts' if per_file else 'total_cnts'
        df = self.dataset.drop_duplicates(['word','lemma'], keep='first')
        
        datasets = [df.loc[df.file == f] for f in set(df.file)] if per_file else [df]
        
        for df in datasets:
            df = df.sort_values(cnt_col, ascending=False)
            
            for file, word, lemma, kana, word_cnt in zip(df.file, df.word, df.lemma, df.kana, df[cnt_col]):
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

                parsed_answer, jisho_kana = self.__parse_answer(answers, common_only=common_only)
                kana = jisho_kana if jisho_kana != '' else kana
                    
                question = f'{word}[{kana}]'
                stem = 'Stem: '+lemma if include_stem and lemma != word else ''
                
                file = file if per_file else None

                # Add Question & Answer to card
                card = genanki.Note(model=self.template, fields=[question, stem, parsed_answer, self.__parse_example(word, lemma, file=file)])
                self.deck.add_note(card)
                
                if min_word_cnt:
                    if word_cnt < min_word_cnt:
                        break
                else:
                    if len(words_added) >= n_most_common:
                        break
                        
        self.words_added = words_added
        self.skipped = skipped
    
    def __parse_example(self, word, lemma, file=None, max_lines=100):
        condition = (self.dataset.word == word) & (self.dataset.lemma == lemma)
        if file:
            condition &= (self.dataset.file == file)
            
        example_list = set(self.dataset.loc[condition, 'line'].values)
        example_list = [e for e in example_list if e != word and e != lemma]
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
    
    def __parse_answer(self, answers, max_lines=100, common_only=True):
        answer_str = ''
        kana = ''
        line_cnt = 0
        for def_idx in range(len(answers)):
            if not answers[def_idx].iscommon:
                continue
                
            if def_idx == 0:
                kana = answers[def_idx].ja[0].reading
            
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
        return answer_str, kana
        
    def _import_ignore_lists(self):
        self.ignore = [l for f in self.ignore_files for l in self._file_to_line_list(f)]
        
    def _import_match_list(self):
        match = []
        for match_file in [f for f in os.listdir(MATCH_DIR) if f.endswith('.txt')]:
            for line in self._file_to_line_list(os.path.join(MATCH_DIR, match_file)):
                for word in line.replace(',', '\n').split('\n'):
                    for token in self._tagger(word):
                        match += [token.surface]
        self.match = match
                
    def _file_to_line_list(self, filename, encoding='utf-8'):
        line_list = []
        with open(filename, 'r', encoding=encoding) as file:
            for line in file:
                line_list += [line.replace('\n', '')]
        return line_list
        
    def _subfile_to_dataset(self, path):
        """
            Returns a dataframe ['file', 'line_idx', 'time', 'line', 'word', 'lemma', 'kana']
            for each index in the subtitle file
        """
        
        lines_indexed = self.__chunk_sub_idx_to_list(self._file_to_line_list(path))

        data = []
        for idx in lines_indexed:
            if len(idx) <= 2:
                continue

            line_idx, timestamp = idx[:2]
            for line in idx[2:]:
                for word in self._tagger(line):
                    if word.surface in self._not_alpha or word.feature.lemma in self._not_alpha or word.is_unk:
                        continue

                    data += [(path, line_idx, word.surface, self.__filter_lemma(word.feature.lemma), word.feature.kana, timestamp, line.strip())]  
    
        return pd.DataFrame(data, columns=self._cols)
        
    def _get_word_counts(self):
        """
            Counts word/lemma pairs for all files and individual files. Then appends ['total_cnts', 'file_cnts'] to dataframe
        """
        
        # Get counts across all subtitles
        #self.dataset.loc[:,'total_cnts'] = self.dataset.loc[:,['word','lemma']].groupby('word').transform('count')
        self.dataset.loc[:, 'word_lemma'] = self.dataset.word + '_'+self.dataset.lemma
        self.dataset.loc[:,'total_cnts'] = self.dataset.groupby('word_lemma')['word_lemma'].transform('count')
        
        
        # Get counts per subtitle file
        self.dataset.loc[:,'file_cnts'] = 0
        for file in set(self.dataset.file):
            filt = self.dataset.loc[self.dataset.file == file]
            #filt['file_cnts'] = filt[['word','lemma']].groupby('word').transform('count') 
            filt.loc[:,'file_cnts'] = filt.groupby('word_lemma')['word_lemma'].transform('count')
            self.dataset.update(filt)
        
        # Convert to int dtype
        self.dataset.loc[:, ['total_cnts', 'file_cnts']] = self.dataset.loc[:, ['total_cnts', 'file_cnts']].astype(int)
        self.dataset = self.dataset.drop(columns=['word_lemma'])
        
    def __filter_lemma(self, text):
        return ''.join([c for c in text if c not in 'abcdefghijklmnopqrstuvwxyz-'])
    
    def __chunk_sub_idx_to_list(self, sub_line_list):
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
    
    def __init_anki_deck(self, deck_name, furigana=True):
        furigana = 'furigana' if furigana else 'kanji'
        qfmt = '<p class="question">{{'+furigana+':Question}}</p><p class="stem">{{Stem}}</p>'

        model_id = random.randrange(1 << 30, 1 << 31)
        template = genanki.Model(
          model_id,
          'SubJapFlash_Model',
          fields=[
            {'name': 'Question'},
            {'name': 'Stem'},
            {'name': 'Answer'},
            {'name': 'Examples'}, 
          ],
          templates=[
            {
              'name': 'SubJapFlash',
              'qfmt': qfmt,
              'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}<hr id="examples">{{Examples}}',
            },
          ],
          css=self.deck_style)

        deck_id = random.randrange(1 << 30, 1 << 31)
        deck = genanki.Deck(
          deck_id,
          deck_name)
        
        self.deck = deck
        self.template = template
    
    def __merge_matching_strings(self, str_list, alpha_only=True):
        str_list = [text[:len(min(str_list))].lower() for text in str_list] # Truncate to min len

        merged = ''
        for i in range(len(str_list[0])):
            idx_chars = [text[i] for text in str_list]
            merged += idx_chars[0] if all([idx_chars[0] == c for c in idx_chars]) else ''
        merged = merged.strip()
        merged = ''.join([c for c in merged if c.isalpha() or c in [' ', '_']]) if alpha_only else merged
        merged = merged.strip(' ').replace(' ', '_').strip('_')
        return merged
        
    def __len__(self):
        return len(self.sub_files)


#def dir_text_to_line_list(directory, ext='.txt'):
#    line_list = []
#    for dir_file in [f for f in os.listdir(directory) if f.endswith(ext)]:
#        line_list += self._file_to_line_list(os.path.join(directory, dir_file))
#    return line_list


 

