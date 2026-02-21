import numpy as np
import pdfplumber

path = "2022 CCI Alphabetic and Tabular List.pdf"
pages = range(68, 69)

def readpdf(path, pages):   
    texts = []
    pages = range(pages.start - 1, pages.stop)
    with pdfplumber.open(path) as pdf:
        for i in pages:
            page = pdf.pages[i]
            text = page.extract_text()
            texts.append(text)
    return texts

# Test
# text = readpdf(path, pages)   
# print(text)

def readtable(path, pages):
    tables_list = []
    pages = range(pages.start - 1, pages.stop)
    with pdfplumber.open(path) as pdf:
        for i in pages:  
            page = pdf.pages[i]
            tables = page.extract_tables()
            for table in tables:
                tables_list.append(np.array(table))
    return tables_list
    
# Test
# tables_list = readtable(path, pages)
# if tables_list:
#     print(tables_list)
# else: print("no table")