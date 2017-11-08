# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from hashlib import sha256

from es import insert_url, insert_data, create_index, search_url

SEED = "http://www.coep.org.in/"

def remove_special_chars(text):
    res = ""
    for c in text:
        # is `c` a letter (upper or lowercase)?
        if (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z'):
            res += c
        # is `c` any punctuation mark or special character?
        elif c in ('.', ',', '!', '@', '#', '&', '*', '+', '/', '%', '(', ')', '[', ']', '-', '_', ':', '?'):
            res += c
        # is `c` a digit?
        elif c.isdigit():
            res += c
        # is `c` an escape character?
        elif c in ('\r', '\f', '\v', '\b', '\t', '\n'):
            res += ' '
        # is `c` a single or double quote?
        #elif c in ('\'', '\"'):
        #    res += '\\\\' + c
        # is `c` a whitespace?
        elif c == ' ' and res:
            if res[-1] != ' ':
                res += c
    return res

def extract_links(doc, seed="http://www.coep.org.in"):
    '''
        returns a list of links to be crawled
    '''
    a_list = doc.find_all('a', href=True)
    links = [el['href'] for el in a_list]
    if len(links) == 0:
        return 0
    nlinks = [] # final list of urls
    for i in range(len(links)):
        if not special_url(links[i]):
            try:
                if links[i][0] == '/' and links[i] != '/' and links[i] != '#': # link is relative
                    nlinks.append(seed + links[i]) # convert relative to absolute
                elif 'coep' in links[i]: # ignore absolute links not containing the term 'coep' in them
                    nlinks.append(links[i])
            except:
                print("Failed in extract_links for", links[i])
                continue

    return nlinks

def special_url(url):
    if url.startswith("mailto") or url.startswith("http://www.coep.org.in/calendar") or url.startswith("http://www.coep.org.in/node") or url.startswith("http://www.coep.org.in/user/") or url.startswith("http://www.coep.org.in/ham/") or url.endswith(".png") or url.endswith(".doc") or url.startswith("http://nextcloud") or url.startswith("https://www.outlook.com") or url.startswith("http://www.outlook.com") or url.startswith("http://kpoint") or url.startswith("http://portal") or url.startswith("https://login") or url.startswith("http://moodle") or url.startswith("http://foss") or url.endswith(".xyz") or url.endswith("#main-content") or url.endswith("javascript:void(0)"):
        return True
    return False

def get_title(doc):
    try:
        return remove_special_chars(doc.find_all('h1')[0].text)
    except:
        pass
    try:
        return remove_special_chars(doc.find_all('h2')[0].text)
    except:
        pass
    try:
        return remove_special_chars(doc.find_all('h3')[0].text)
    except:
        pass
    try:
        return remove_special_chars(doc.find_all('h4')[0].text)
    except:
        pass
    return "DEFAULT_TITLE"

def get_content(doc):
    '''
        returns all text between <span> and <p> tags
    '''
    # find title
    title = get_title(doc) 

    span_text_list = doc.find_all('span') # find all span tags
    span_text = set() # insert into a set as sometimes span elements repeat
    for el in span_text_list:
        if len(el.text):
            span_text.add(el.text)
    #span_text = ". ".join(span_text)
    #span_text = remove_special_chars(span_text)#.encode('utf8')
    
    p_text_list = doc.find_all('p') # find all span tags
    #p_text = [el.text for el in p_text_list] # get text between span tags
    for el in p_text_list:
        if len(el.text):
            span_text.add(el.text)
    #p_text = " ".join(p_text) # string of all span texts
    #p_text = remove_special_chars(p_text)#.encode('utf8') # convert unicode to string
    final = remove_special_chars(" ".join(span_text))
    return title, final

    if len(span_text) > len(p_text):
        return title, span_text + ' ' + p_text
    return title, p_text + ' ' + span_text

def sha256_checksum(text):
    # find sha256 hash of a string
    # convert text to bytes
    text = bytes(text.encode())
    return sha256(text).hexdigest()
#glob_links = set()
def remove_duplicate_links(links, prev_links):
    res_l = []
    for link in links:
        #if (link in glob_links) or (link in prev_links):
        if (link in prev_links):
            continue
        elif link.endswith(".pdf"):
            continue
        else:
            res_l.append(link)
    return res_l

def crawl(seed):
    print("Crawl", seed)
    req_sess = requests.Session() # create a session for faster GET
    
    try:
        resp = req_sess.get(seed, timeout=3)
        print(resp)
    except requests.exceptions.ConnectionError as e:
        print(seed)

    if resp.status_code != 200: # 200 OK
        print("***", seed, resp.status_code)
        exit()
    
    doc = BeautifulSoup(resp.text, 'html.parser')
    links = [seed]
    # get all links in doc
    links += extract_links(doc)
    #for link in links:
    #    glob_links.add(link)
    
    for idx, link in enumerate(links):
        if "download/file/fid" in link: # these always give 404
            continue
        elif link[-4:] == ".pdf": # PDF file
            continue
        elif "facebook" in link:
            continue
        elif "/node" in link:
            continue
        elif "www.sedo.com" in link:
            continue
        print("_______________")
        print(str(float(idx) / len(links) * 100) + "% done", idx, len(links), link)
        #glob_links.add(link)
        try:
            resp = req_sess.get(link+'/', timeout=3)
            if resp.text[:4] == "%PDF": # resp is a PDF file
                continue
            if resp.status_code != 200:
                print("***", link, resp.status_code)
                continue
        except requests.exceptions.ConnectionError as e:
            print(link, "timed out")
            continue
        except requests.exceptions.ReadTimeout:
            print(link, "read timed out")
            continue
        except:
            continue

        doc = BeautifulSoup(resp.text, 'html.parser')
        
        title, body = get_content(doc)
        
        # find sha256 checksum of title and body
        chksum = sha256_checksum(title+body)
        
        new_links = extract_links(doc) # extract new links on link page
        
        if new_links:
            new_links = remove_duplicate_links(new_links, links)
            if new_links:
                links += new_links # append new links to links
        present, res = search_url(link)
        
        if present: # url is present in the `duplicate_urls` index
            # check the checksum
            try:
                if res["hits"]["total"] == 1:
                    prev_chksum = res["hits"]["hits"][0]["_source"]["checksum"]
                    if prev_chksum == chksum:
                        continue
                    else:
                        _id = res["hits"]["hits"][0]["_id"]
                        stat = delete_page(_id)
                else:
                    print("Multiple records found", link)
                    print("res", res)
                    exit()
            except TypeError:
                continue
        else:
            # insert url and document
            stat = insert_url(link, chksum)
            if not stat:
                print("Link insertion failed", link)
                continue
        stat = insert_data(link, title, body)
        if not stat:
            print("Data insertion failed", link)

create_index()
crawl(SEED)
