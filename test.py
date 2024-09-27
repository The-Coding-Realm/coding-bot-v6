import re


def filter_banned_words(text: str):
    with open("storage/banned_word.txt") as f:
        words = f.read().split(", ")
    
    new_text = text
    for word in words:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        
        def censor(match):
            matched_word = match.group()
            word_length = len(matched_word) // 2
            stars = "*" * word_length
            return f"{stars}{matched_word[word_length:]}"
        
        new_text = pattern.sub(censor, new_text)

    return new_text

text = "Niggas"
censored_text = filter_banned_words(text)
print(censored_text)