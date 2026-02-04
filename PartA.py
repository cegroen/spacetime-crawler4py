import re
import sys

# the runtime is O(n) where n is the number of characters in the input because all of them
# need to be iterated through
def tokenize(txt):
    token_list = []

    line = txt.strip()
    line = line.lower()
    token_list.extend(
        token
        for token in re.findall(r'\b\w+\b', line)
        if token.isascii() and token.isalnum()
    )

    return token_list

# this runs in expected time O(n) where n is the number of tokens because as we iterate once 
# through the list of tokens we do a dictionary lookup and insertion for each one
def computeWordFrequencies(tokens):
    freq_dict = {}
    for token in tokens:
        if token in freq_dict:
            freq_dict[token] += 1
        else: freq_dict[token] = 1
        
    return freq_dict

# this runs in time O(nlogn) where n is the number of distinct tokens because it requires sorting
def printnew(freqs):
    items = freqs.items()
    sorted_items = sorted(items, key=lambda item: item[1], reverse=True)
    print(sorted_items)

if __name__ == "__main__":
    file = sys.argv[1]
    tokens = tokenize(file)
    frequencies = computeWordFrequencies(tokens)
    printnew(frequencies)
