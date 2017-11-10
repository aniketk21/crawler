# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from hashlib import sha256

from es import insert_url, insert_data, create_index, search_url
from pdf_extract import pdf_caller

SEED = "http://www.coep.org.in/"
TIMEOUT = 15

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
                elif "coep.org" in links[i]: # ignore absolute links not containing the "coep.org" in them
                    nlinks.append(links[i])
            except:
                print("Failed in extract_links for", links[i])
                continue

    return nlinks

starts = ["mailto", "http://www.coep.org.in/calendar", "http://www.coep.org.in/node", "http://www.coep.org.in/user", "http://www.coep.org.in/ham/", "http://nextcloud", "http://www.outlook.com", "https://www.outlook.com", "http://kpoint", "http://portal", "https://login", "http://moodle", "http://foss"]
ends = [".png", ".jpg", ".jpeg", ".doc", ".xyz", ".zip", ".war", ".gz", ".tar.gz", "#main-content", "javascript:void(0)"]
misc = ["download/file/fid", "facebook", "twitter", "/node", "www.sedo.com"]

def special_url(url):
    # check whether url starts with any element in `starts`
    for spc_url in starts:
        if url.startswith(spc_url):
            return True
    
    # check whether url ends with any element in `ends`
    for spc_url in ends:
        if url.endswith(spc_url):
            return True

    # check misc
    for term in misc:
        if term in url:
            return True
    
    return False

def get_title(doc):
    # extract the document's title
    try:
        title = remove_special_chars(doc.find_all('title')[0].text)
        ntitle = title[:-28] # to remove "College of Engineering, Pune" as it occurs in all titles
        if len(ntitle) < 3:
            return title
        return ntitle
    except:
        return "DEFAULT_TITLE"

def get_content(doc):
    '''
        returns all text between <span> and <p> tags
    '''
    # find title
    title = get_title(doc) 

    # find all span tags
    span_text_list = doc.find_all('span')
    span_text = set() # insert into a set as sometimes span elements repeat
    for el in span_text_list:
        if len(el.text):
            span_text.add(el.text)
    
    # find all p tags
    p_text_list = doc.find_all('p')
    for el in p_text_list:
        if len(el.text):
            span_text.add(el.text)
    
    final_text = remove_special_chars(" ".join(span_text))
    
    return title, final_text

def sha256_checksum(text):
    # find sha256 hash of a string
    # convert text to bytes as `sha256` requires `bytes` input
    text = bytes(text.encode())
    return sha256(text).hexdigest()

def remove_already_seen_links(links, prev_links):
    res = []
    
    for link in links:
        # if `link` has been seen previously
        if link in prev_links:
            continue
        else:
            res.append(link)

    return res

# main crawl code
def crawl(seed):
    print("Crawling", seed)
    
    # create a requests session for faster GET
    req_sess = requests.Session()
    resp = None 
    try:
        resp = req_sess.get(seed, timeout=TIMEOUT)
        print(seed, resp)
        if resp.status_code != 200: # 200 OK
            print("***", seed, resp.status_code)
            exit()
    except:
        if resp:
            print(seed, resp, resp.text)
        else:
            print(seed, resp)
        exit()

    doc = BeautifulSoup(resp.text, 'html.parser')
    
    # list of all links
    links = [seed]

    # get all links in doc
    links += extract_links(doc)
    
    crawled_cntr = 1

    for idx, link in enumerate(links):
        if idx == 0:
            continue

        PDF_FLAG = False
        
        print("--------------------")
        print("%.2f"%(float(idx)/len(links)*100)+"% done | ("+str(idx)+"/"+str(len(links))+") | "+link)
        
        try:
            resp = req_sess.get(link, timeout=TIMEOUT)
 
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
        
        # check if resp is a PDF file
        if (resp.text[:4] == "%PDF") or (link[-4:] == ".pdf"):
            PDF_FLAG = True

            pdftext = pdf_caller(link, req_sess)
            if (pdftext is None) or (len(pdftext) < 5):
                continue

            body = remove_special_chars(pdftext)

            title = link.split('/')[-1].replace("%20", ' ').replace(".pdf", '')
                
            #stat = insert_data(link, title, body)
            #if not stat:
            #    print("Data insertion failed", link)
            # 
            #continue
        
        if not PDF_FLAG:
            doc = BeautifulSoup(resp.text, 'html.parser')
        
            title, body = get_content(doc)
            
            # extract new links on link page
            new_links = extract_links(doc)

            if new_links:
                new_links = remove_already_seen_links(new_links, links)
                if new_links:
                    links += new_links # append new links to links

        # find sha256 checksum of title and body
        chksum = sha256_checksum(title+body)

        # search whether link is already present in ES
        present, res = search_url(link)
        
        if present: # url is present in the `duplicate_urls` index
            # check the previous and current checksum
            print("url exists")
            try:
                if res["hits"]["total"] == 1:
                    # find previously stored checksum
                    prev_chksum = res["hits"]["hits"][0]["_source"]["checksum"]
                    
                    if prev_chksum == chksum:
                        continue
                    
                    else:
                        _id = res["hits"]["hits"][0]["_id"]
                        stat = delete_page(_id)
                
                else:
                    print("Multiple records found", link)
                    print("res", res)
                    continue

            except TypeError:
                continue
        
        else:
            # insert url and document
            stat = insert_url(link, chksum)
            if not stat:
                print("Link insertion failed", link)
                continue
        
        stat = insert_data(link.encode('utf-8'), title.encode('utf-8'), body.encode('utf-8'))
        if not stat:
            print("Data insertion failed", link)
            continue

        crawled_cntr += 1
    return crawled_cntr

def main():
    create_index()
    total_crawled = crawl(SEED)
    print("____________________")
    print("* Successfully crawled %d URLs *" % total_crawled)
    print("____________________")

if __name__ == "__main__":
    main()
