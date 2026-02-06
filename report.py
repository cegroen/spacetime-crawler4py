import pickle
import os

report_file = "report.pkl"

if not os.path.exists(report_file):
    raise SystemExit

with open(report_file, "rb") as f:
    data = pickle.load(f)

stop_words = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"]

unique_pages = data["unique_pages"]
subdomains = data["subdomains"]
word_freq = data["word_freq"]
longest_page = data["longest_page"]

sorted_subdomains = dict(sorted(subdomains.items()))

print("Unique pages so far:", len(unique_pages))
print("\nLongest page so far:", longest_page)
print("\nNumber of subdomains:", len(subdomains))

# Print all subdomains in alphabetical order
for subdomain, count in sorted(subdomains.items(), key=lambda x: x[0]):
    print(subdomain, count)

sorted_words = sorted(
    word_freq.items(),
    key=lambda kv: kv[1],
    reverse=True
)

print("\nTop 50 words:")
count = 0
for w, c in sorted_words:
    if w.lower() not in stop_words:
        print(w, c)
        count += 1
        if count >= 50:
            break
        