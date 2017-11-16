# _Web Crawler_
A web crawler for http://www.coep.org.in  
Crawls webpages and PDF files.  
Stores text in Elasticsearch.  
Uses SHA256 checksum to avoid indexing duplicate pages.  

# Execution
`$ python3 crawler.py`  
This will create indices (if they don't exist) and would start crawling SEED_URL (default is http://www.coep.org.in)

# Structure
  - _crawler.py_ : Main crawler code  
  - _pdf_extract.py_ : Download and then extract text from a PDF file  
  - _es.py_ : Create Indices, Insert URLs and data, Delete pages in Elasticsearch  

# Algorithm  
 
	CRAWL(seed_url)
		doc := GET seed_url
		
		links := Extract all hyperlinks from doc
		
		for link in links:
			doc := GET link
			
			if doc is a PDF file:
				title := title of PDF file
				body := EXTRACT_TEXT_FROM_PDF(doc)
			else:
				title, body := get title and body from doc
				new_links := new links found in the doc  //which are not already in the links list
				links := APPEND(links, new_links)
			
			checksum := SHA256_CHECKSUM([title, body])
			
			present := SEARCH_URL(link) //check whether link is present in Elasticsearch
			
			if present:
				get previously stored checksum
				if previous checksum and new checksum match:
					continue
				else:
					delete page from Elasticsearch
			else:
				insert url and checksum in Elasticsearch
			
			insert the page in Elasticsearch

## _crawler.py_
  |__ **main()** - main function, calls crawl  
  |  
  |__ **crawl(seed)** - crawler code  
  |  
  |__ **get_title(doc)** - get title of the HTML document  
  |  
  |__ **get_content(doc)** - get text between `<p>` and `<span>` tags in the HTML document  
  |  
  |__ **remove_special_chars(text)** - remove non-ASCII characters from the text  
  |  
  |__ **extract_links(doc, seed=SEED_URL)** - extract links between `<a>` tags, convert relative urls to absolute urls  
  |  
  |__ **special_url(url)** - don't crawl urls like http://outlook.com/, http://foss.coep.org.in, etc  
  |  
  |__ **sha256_checksum(text)** - return SHA256 checksum of text  
  |  
  |__ **remove_already_seen_links(links, prev_links)** - remove links which are already present in the links list  

## _es.py_
  |__ **create_index()** - create two indices viz. `duplicate_urls` and `web_dump`  
  |  
  |__ **insert_url(url, checksum)** - insert the url and checksum into ES  
  |  
  |__ **insert_data(link, title, body)** - insert page into ES  
  |  
  |__ **search_url(url)** - return True if url exists in ES `duplicate_urls` index  
  |  
  |__ **delete_page(_id)** - delete the page with ID = _id from ES `web_dump` index  

## _pdf_extract.py_
  |__ **download_file(url, req_sess)** - download file from URL  
  |  
  |__ **extract_text_from_pdf(fname)** - extract text from file `fname` and then delete the PDF file  
  |  
  |__ **pdf_caller(url, req_sess)** - calls above two functions  
  
# Dependencies:
  - Python 3  
  - Elasticsearch >= 5.5
  - requests  
  - beautifulsoup 4  
  - pdfminer.six  
