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
    
    base = "http://localhost:9200/web_dump/dump"
    
    try:
        link = '"link": "' + link.decode('utf-8') + '",'
        title = '"title": "' + title.decode('utf-8') + '",'
        body = '"body": "' + body.decode('utf-8') + '"'
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
    
    except:
        pass
    
    return False

def create_index():
    '''
        create the index in ES
        ES
        |_duplicate_urls
        |   |_url
        |_web_dump
    '''
    base = "http://localhost:9200/duplicate_urls"
    payload = '{"mappings": {"duplicate_urls": {"properties": {"link": {"type": "string", "index": "not_analyzed"}, "checksum": {"type": "string", "index": "not_analyzed"}}}}}'
    headers = {'content-type': 'application/json'}
    
    r = requests.put(url=base, data=payload, headers=headers)
    
    if not(r.status_code in [200, 400]): # 200 OK, 400 "already exists"
        print("Index creation failed")
        print(base, r, r.text)
        exit()

    base = "http://localhost:9200/web_dump"
    payload = '{"mappings": {"web_dump": {"properties": {"title" : {"type": "string", "index": "not_analyzed"}}}}}'
    headers = {'content-type': 'application/json'}
    
    r = requests.put(url=base, headers=headers)
    
    if not(r.status_code in [200, 400]): # 200 OK, 400 "already exists"
        print("Index creation failed")
        print(base, r, r.text)
        exit()

def search_url(url):
    '''
        search the `url` in ES
    '''
    base = "http://localhost:9200/duplicate_urls/url/_search"
    payload = '{"query": {"constant_score": {"filter": {"term": {"link": "' + url + '"}}}}}'
    headers = {'content-type': 'application/json'}
    
    res = requests.get(url=base, data=payload, headers=headers)
    
    if res.status_code == 200: # 200 OK
        if res.json()['hits']['total'] == 1: # url was found in ES
            return True, res
    return False, res.json()

def delete_page(_id):
    '''
        delete the page with id=_id from web_dump
    '''
    base = "https://localhost:9200/web_dump/dump/" + _id
    payload = '{}'
    headers = {'content-type': 'application/json'}
    
    res = requests.delete(url=base, data=payload, headers=headers)
    
    return
