from read_pdf import readpdf

path = "2022 CCI Alphabetic and Tabular List.pdf"
pages = range(69, 69)

text = readpdf(path, pages)
print(text)