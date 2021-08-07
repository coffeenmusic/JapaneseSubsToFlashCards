import genanki
import random

def merge_matching_strings(str_list, alpha_only=True):
    str_list = [text[:len(min(str_list))].lower() for text in str_list] # Truncate to min len
    
    merged = ''
    for i in range(len(str_list[0])):
        idx_chars = [text[i] for text in str_list]
        merged += idx_chars[0] if all([idx_chars[0] == c for c in idx_chars]) else ''
    merged = merged.strip()
    merged = ''.join([c for c in merged if c.isalpha() or c in [' ', '_']]) if alpha_only else merged
    merged = merged.strip().replace(' ', '_') 
    return merged
    
deck_style = """
    .card {
     font-size: 16px;
     text-align: left;
     color: black;
     background-color: white;
    }
    .question {
     font-size: 64px;
     text-align: center;
    }
    """
    
def init_anki_deck(deck_name):
    model_id = random.randrange(1 << 30, 1 << 31)
    template = genanki.Model(
      model_id,
      'SubJapFlash_Model',
      fields=[
        {'name': 'Question'},
        {'name': 'Answer'},
      ],
      templates=[
        {
          'name': 'Card 1',
          'qfmt': '<p class="question">{{Question}}</p>',
          'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
        },
      ],
      css=deck_style)

    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(
      deck_id,
      deck_name)
      
    return deck, template