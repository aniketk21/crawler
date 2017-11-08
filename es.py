# -*- coding: utf-8 -*-
import requests
def insert_url(url, checksum):
    '''
        insert the `url` and its `checksum` in ES
    '''
    base = "http://localhost:9200/duplicate_urls/url"
    payload = '{"link": "'+url+'", ' + '"checksum": "'+checksum+'"}'
    headers = {'content-type': 'application/json'}
    r = requests.post(url=base, data=payload, headers=headers)
    if r.status_code == 201: # 201 Created
        return True
    print(url, r, r.text)
    return False

def insert_data(link, title, body):
    #print("insert"
    base = "http://localhost:9200/web_dump/dump"
    link = '"link": "' + link + '",'
    title = '"title": "' + title + '",'
    body = '"body": "' + body + '"'
    #print(link, type(link)
    #print(title, type(title)
    #print(body, type(body)
    payload = '{' + link + title + body + '}'
    #print(payload
    headers = {'content-type': 'application/json'}
    r = requests.post(url=base, data=payload, headers=headers)
    if r.status_code == 201: # 201 Created
        return True
    print(r, r.text)
    return False

def create_index():
    '''
        create the index in ES
        ES
        |_duplicate_urls
        |   |_url
        |   |_robots
        |_web_dump
    '''
    base = "http://localhost:9200/duplicate_urls"
    payload = '{"mappings": {"duplicate_urls": {"properties": {"link": {"type": "string", "index": "not_analyzed"}, "checksum": {"type": "string", "index": "not_analyzed"}}}}}'
    headers = {'content-type': 'application/json'}
    r = requests.put(url=base, data=payload, headers=headers)
    #print(base, r
    #print(r.text
    #if r.status_code in [200, 400]: # 200 OK, 400 "already exists"
    #    return True
    base = "http://localhost:9200/web_dump"
    payload = '{"mappings": {"web_dump": {"properties": {"title" : {"type": "string", "index": "not_analyzed"}}}}}'
    headers = {'content-type': 'application/json'}
    r = requests.put(url=base, headers=headers)
    #print(base, r
    #print(r.text
    #if r.status_code in [200, 400]: # 200 OK, 400 "already exists"
    #    return True

def search_url(url):
    '''
        search the `url` in ES
    '''
    base = "http://localhost:9200/duplicate_urls/url/_search"
    payload = '{"query": {"constant_score": {"filter": {"term": {"link": "' + url + '"}}}}}'
    # testcase
    #base = "http://localhost:9200/my_store/products/_search"
    #payload = '{"query": {"constant_score": {"filter": {"term": {"productID": "XHDK-A-1293-#fJ3"}}}}}'
    headers = {'content-type': 'application/json'}
    res = requests.get(url=base, data=payload, headers=headers)
    #print(r.text
    if res.status_code == 200: # 200 OK
        if res.json()['hits']['total'] == 1: # url was found in ES
            return True, res
    return False, res.json()

def delete_page(_id):
    base = "https://localhost:9200/web_dump/dump/" + _id
    payload = '{}'
    headers = {'content-type': 'application/json'}
    res = requests.delete(url=base, data=payload, headers=headers)
    return
