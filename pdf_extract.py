import os

from io import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

def download_file(url, req_sess):
    local_filename = url.split('/')[-1]
    #print(local_filename)
    r = None
    try:
        r = req_sess.get(url, stream=True)
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
    
        return local_filename
    
    except:
        if r:
            print(url, r, r.text)
        return None

def extract_text_from_pdf(fname, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    try:
        output = StringIO()
        manager = PDFResourceManager()
        converter = TextConverter(manager, output, laparams=LAParams())
        interpreter = PDFPageInterpreter(manager, converter)

        infile = open(fname, 'rb')
    
        for page in PDFPage.get_pages(infile, pagenums):
            interpreter.process_page(page)
    
        infile.close()
        converter.close()
        text = output.getvalue()
        output.close
        os.remove(fname)
    
        return text
    
    except Exception as e:
        print(fname, e)
        return None

def pdf_caller(url, req_sess):
    fname = download_file(url, req_sess)
    
    if fname is None:
        return None
    
    return extract_text_from_pdf(fname)
