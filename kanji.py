import requests
from bs4 import BeautifulSoup
import csv

file = open("sample.csv", "w", newline='', encoding='utf-8')
writter = csv.writer(file)

for i in range(1036, 1046):
    url = url = "https://nihongokanji.com/{}".format(i)
    print("Requesting... {}".format(url))
    response = requests.get(url)
    #print(response.status_code)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    head = soup.find("div", id="head").find("a")
    contents = soup.find_all("ul")
    
    mean_type = len(contents[4].find_all("li"))
    meanings = contents[4].find_all("b")
    
    index = head.text[:4]
    level = "N1"
    kanji = head.text[-2]
    
    mean = meanings[0].text[4:]
    position = mean.find('.')
    korean_onkun = mean[1:position-1]
    korean_mean = mean[position+2:]
    on_yomi = meanings[1].text[4:]
    
    if mean_type == 2:    
        kun_nyomi = "-"
    else:
        kun_nyomi = meanings[2].text[4:]
    
    writter.writerow([index, level, str(kanji), korean_onkun, korean_mean, str(on_yomi), str(kun_nyomi), url])
print("done.")

