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