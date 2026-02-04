import pickle
import os

report_file = "report.pkl"

if not os.path.exists(report_file):
    print("No analytics file found yet.")
    raise SystemExit

with open(report_file, "rb") as f:
    data = pickle.load(f)

unique_pages = data["unique_pages"]
subdomains = data["subdomains"]
word_freq = data["word_freq"]
longest_page = data["longest_page"]

sorted_subdomains = dict(sorted(subdomains.items()))

print("Unique pages so far:", len(unique_pages))
print("Longest page so far:", longest_page)

# Show a few subdomains
ics_subdomains = {
    url: count for url, count in subdomains.items()
    if url.endswith("ics.uci.edu")
}
print("Number of ics.uci.edu subdomains:", len(ics_subdomains))

for subdomain, count in list(ics_subdomains.items())[:10]:
    print(subdomain, count)

# Top 10 words
top_words = sorted(
    word_freq.items(),
    key=lambda kv: kv[1],
    reverse=True
)[:10]
print("\nTop 10 words so far:")
for w, c in top_words:
    print(w, c)