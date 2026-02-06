import re
from urllib.parse import urlparse, urljoin, urldefrag
from lxml import html
import PartA
import pickle
import os
from collections import deque
from difflib import SequenceMatcher

unique_pages = set()
longest_page = ("", 0)
word_freq = {}
subdomains = {}
counter = 0
report_file = "report.pkl"
recent_pages = deque(maxlen = 50)
recent_urls = deque(maxlen = 400)
too_similar = 0.9

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scraped from resp.raw_response.content

    global unique_pages, longest_page, word_freq, subdomains, counter, report_file, recent_pages, too_similar
    
    links = []
    counter += 1

    if resp.status != 200:
        return links

    # detect and avoid dead URLs that return a 200 status but no data
    if not resp or not resp.raw_response or not resp.raw_response.content:
        return links

    content_type = resp.raw_response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        return links

    try:
        tree = html.fromstring(resp.raw_response.content)
    except Exception:
        return links
    
    # get rid of text in style and script tags
    for tag in tree.xpath("//script | //style"):
        tag.getparent().remove(tag)

    text = tree.text_content()

    # check for very low information
    if len(text) <= 200:
        return links

    tokens = PartA.tokenize(text)
    token_set = set(tokens)
    word_count = len(tokens)

    # check for similarity to previous pages by computing Jaccard similarity of tokens
    for (_, other_tokens) in recent_pages:
        if jaccard_similarity(token_set, other_tokens) >= too_similar:
            return links # return if page is too similar
    
    recent_pages.append((url, set(tokens))) # add to recent_pages if it wasn't similar to anything
    recent_urls.append(url)

    if word_count > longest_page[1]: longest_page = (url, word_count)

    # keep track of word frequencies in a dictionary
    for token in tokens:
        if token in word_freq: word_freq[token] += 1
        else: word_freq[token] = 1
        
    print('------------------------------- Actually crawling this site -------------------------------')

    # find outgoing links
    for element in tree.xpath("//a[@href]"):
        href = element.get("href")
        if href is None:
            continue

        absolute_url = urljoin(url, href)
        absolute_url, _ = urldefrag(absolute_url)

        if absolute_url not in unique_pages:
            unique_pages.add(absolute_url)
            links.append(absolute_url)
            #parsed = urlparse(url)
            parsed = urlparse(absolute_url) # not sure about this but im supposed to compute the # of unique pages detected not necessarily downloaded
            host = parsed.hostname or ""

            # keep track of visited subdomain frequencies
            if host.endswith("ics.uci.edu"):
                subdomain_key = f"http://{host}"
                if subdomain_key in subdomains:
                    subdomains[subdomain_key] += 1
                else:
                    subdomains[subdomain_key] = 1            

    # write data to file after certain number of iterations
    if counter >= 50:
        data = {
            "unique_pages": unique_pages,
            "subdomains": subdomains,
            "word_freq": word_freq,
            "longest_page": longest_page,
        }
        temp = report_file + ".tmp" # temp file so I don't try to access the file while it is being written
        with open(temp, "wb") as f:
            pickle.dump(data, f)
        os.replace(temp, report_file)
        counter = 0

    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    global recent_urls

    try:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            return False

        host = parsed.hostname or ""
        path = parsed.path or ""
        netloc = host.lower()

        allowed = False

        if netloc.endswith("ics.uci.edu"):
            allowed = True
        elif netloc.endswith("cs.uci.edu"):
            allowed = True
        elif netloc.endswith("informatics.uci.edu"):
            allowed = True
        elif netloc.endswith("stat.uci.edu"):
            allowed = True
        elif netloc == "today.uci.edu":
            if not path.startswith("/department/information_computer_sciences"):
                return False
            allowed = True

        if not allowed:
            return False
        
        lowered_path = path.lower()
        login_words = ["login", "signin", "logout", "admin", "account", "auth"]

        if any(k in lowered_path for k in login_words):
            return False

        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            r"|png|tiff?|mid|mp2|mp3|mp4"
            r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            r"|epub|dll|cnf|tgz|sha1"
            r"|thmx|mso|arff|rtf|jar|csv"
            r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",
            path.lower()
        ):
            return False

        # avoid extremely long urls
        if len(url) > 200:
            return False

        # avoid repeated segments and long sequences of segments
        segments = [seg for seg in path.split("/") if seg]
        if len(segments) != len(set(segments)) and len(segments) > 6:
            return False

        # 3. Avoid certain query patterns that tend to be traps
        trap_words = [
            "calendar", "ical", "month", "year", "eventdisplay,", "date", "login"
        ]
        query = parsed.query.lower()
        if query:
            # try to avoid calendars and other traps
            if any(k in query for k in trap_words):
                return False

            # avoid urls with many query parameters
            if query.count("&") >= 5:
                return False
            
            # avoid these files in queries as well
            if re.search(
                r"(=|%3a)[^=&]+\.(css|js|bmp|gif|jpe?g|ico"
                r"|png|tiff?|mid|mp2|mp3|mp4"
                r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                r"|epub|dll|cnf|tgz|sha1"
                r"|thmx|mso|arff|rtf|jar|csv"
                r"|rm|smil|wmv|swf|wma|zip|rar|gz)",
                query
            ):
                return False
            
        # check url similarity
        for other_url in recent_urls:
            if SequenceMatcher(None, url, other_url).ratio() >= 0.9:
                return False
            
        recent_urls.append(url)

        return True

    except TypeError:
        print("TypeError for ", url)
        return False
    
# for computing similarity of two sets of tokens
def jaccard_similarity(set1, set2):
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    if union == 0:
        return 0.0
    return intersection / union
    