import re

pattern = "(\d+\.[A-Za-z]{2}\.\d{2})\.\^\^\s+(.+)" 
def regex_json (text, pattern): 
    match = re.search(pattern, text)
    if match:
        code = match.group(1)
        description = match.group(2).strip()
    return (code, description)
    
user_input = input("Input your sequence: ")
code, description = regex_json(user_input, pattern)
if(re.search(pattern, user_input)):
    print(code, ":", description)
else: print("ehh")