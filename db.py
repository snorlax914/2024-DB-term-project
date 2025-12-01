import psycopg2
import csv

file = open("sample.csv", "r", newline='', encoding='utf-8')
csv_reader = csv.reader(file)

if __name__ == '__main__':
    con = psycopg2.connect(
        database = 'japanese',
        user = 'db2024',
        password = '1234',
        host = '::1',
        port = '5432',
        client_encoding='UTF8'
    )
    cursor = con.cursor()
    
    for line in csv_reader:
        index = line[0]
        level = line[1]
        kanji = line[2]
        korean_onkun = line[3]
        meaning = line[4]
        on_yomi = line[5]
        kun_yomi = line[6]
        link = line[7]
        sqlq = """
        INSERT INTO kanji(index, level, kanji, korean_onkun, meaning, on_yomi, kun_yomi, link)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sqlq, (index, level, kanji, korean_onkun, meaning, on_yomi, kun_yomi, link))
        
    con.commit()