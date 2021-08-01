def merge_matching_strings(str_list):
    str_list = [text[:len(min(str_list))].lower() for text in str_list] # Truncate to min len
    
    merged = ''
    for i in range(len(str_list[0])):
        idx_chars = [text[i] for text in str_list]
        merged += idx_chars[0] if all([idx_chars[0] == c for c in idx_chars]) else ''
    return merged