from read_pdf import readpdf

path = "2022 CCI Alphabetic and Tabular List.pdf"
pages = range(68, 69)

text = readpdf(path, pages)
print(text[1])