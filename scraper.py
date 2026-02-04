import re
from urllib.parse import urlparse, urljoin, urldefrag
from lxml import html
import PartA
import pickle
import os

unique_pages = set()
longest_page = ("", 0)  # (url, word_count)
word_freq = {}
subdomains = {}
counter = 0
report_file = "report.pkl"

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
    links = []
    counter += 1

    if resp.status != 200:
        return links

    if not resp.raw_response or not resp.raw_response.content:
        return links

    content_type = resp.raw_response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        return links

    try:
        tree = html.fromstring(resp.raw_response.content)
    except Exception:
        return links

    # words = text.split()
    tokens = PartA.tokenize(tree.text_content())
    word_count = len(tokens)

    # TODO: update global stats here
    if word_count > longest_page[1]: longest_page = (url, word_count)

    for token in tokens:
        if token in word_freq: word_freq[token] += 1
        else: word_freq[token] = 1

    for element in tree.xpath("//a[@href]"):
        href = element.get("href")
        if href is None:
            continue

        absolute_url = urljoin(url, href)
        absolute_url, _ = urldefrag(absolute_url)

        # if is_valid(absolute_url):
        #     links.append(absolute_url)

        # check if we've already seen this page
        if absolute_url not in unique_pages:
            links.append(absolute_url)
            parsed = urlparse(url)
            host = parsed.hostname or ""
            if host.endswith("ics.uci.edu"):
                subdomains[f"http://{host}"] += 1

    if counter >= 400:
        data = {
            "unique_pages": unique_pages,
            "subdomains": subdomains,
            "word_freq": word_freq,
            "longest_page": longest_page,
        }
        temp = report_file + ".tmp"
        with open(temp, "wb") as f:
            pickle.dump(data, f)
        os.replace(temp, report_file)
        counter = 0

    return links

# def is_valid(url):
#     # Decide whether to crawl this url or not. 
#     # If you decide to crawl it, return True; otherwise return False.
#     # There are already some conditions that return False.
#     try:
#         parsed = urlparse(url)
#         if parsed.scheme not in set(["http", "https"]):
#             return False
#         return not re.match(
#             r".*\.(css|js|bmp|gif|jpe?g|ico"
#             + r"|png|tiff?|mid|mp2|mp3|mp4"
#             + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
#             + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
#             + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
#             + r"|epub|dll|cnf|tgz|sha1"
#             + r"|thmx|mso|arff|rtf|jar|csv"
#             + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

#     except TypeError:
#         print ("TypeError for ", parsed)
#         raise

def is_valid(url):
    """
    Decide whether to crawl this URL or not.

    Returns:
        True if we want to crawl this URL, False otherwise.
    """
    try:
        parsed = urlparse(url)

        # Only http/https
        if parsed.scheme not in {"http", "https"}:
            return False

        # ---------- Domain & path filtering ----------
        host = parsed.hostname or ""
        path = parsed.path or ""
        netloc = host.lower()

        # Allowed domains
        # *.ics.uci.edu/*
        # *.cs.uci.edu/*
        # *.informatics.uci.edu/*
        # *.stat.uci.edu/*
        # today.uci.edu/department/information_computer_sciences/*
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
            # Restrict to the required path
            if not path.startswith("/department/information_computer_sciences"):
                return False
            allowed = True

        if not allowed:
            return False

        # ---------- File type filtering (non-HTML resources) ----------
        # If the path looks like a file with disallowed extension, skip it.
        # NOTE: This is similar to the starter, but you can tweak/extend.
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

        # ---------- Basic trap heuristics ----------

        # 1. Extremely long URLs are often traps (e.g., calendars with many params)
        if len(url) > 300:
            return False

        # 2. Repeated path segments (e.g. /2020/01/01/2020/01/01/)
        # can indicate infinite hierarchical traps
        segments = [seg for seg in path.split("/") if seg]
        if len(segments) != len(set(segments)) and len(segments) > 6:
            # Many repeated segments
            return False

        # 3. Avoid certain query patterns that tend to be traps
        query = parsed.query.lower()
        if query:
            # Avoid infinite calendars, search results pages, etc.
            trap_keywords = [
                "calendar", "ical", "month", "year", "format=xml",
                "replytocom", "sessionid", "sort=", "page=", "offset=",
                "limit=", "view=grid", "eventdisplay"
            ]
            if any(k in query for k in trap_keywords):
                return False

            # Too many query parameters can be a trap
            if query.count("&") > 5:
                return False

        return True

    except TypeError:
        print("TypeError for ", url)
        return False
    