from pypdf import PdfReader as pdf
import numpy as np

path = "2022 CCI Alphabetic and Tabular List.pdf"
pages = range(68, 69)

def readpdf(path, pages):   
    text = np.array([])
    pages = range(pages.start - 1, pages.stop)
    read = pdf(path)
    subset = [read.pages[i] for i in pages]
    for page in subset:
        text = np.append(text, page.extract_text())
    return text

text = readpdf(path, pages)
print(text[0])