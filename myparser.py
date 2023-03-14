import bs4
import requests
from mydb import DataBase

class TheParser:
    def __init__(self, db: DataBase):
        self.db = db
        self.payload = {'order':'BY_SOLVED_DESC'}
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "Accept-Language": "ru"}
        self.soup = self.get_page_soup()
        print("Parser Initialized\n*\n**\n***\n**\n*")

    def get_page_soup(self, page_number=1):
        url = "https://codeforces.com/problemset/page/%s" % page_number
        page = requests.get(url, params=self.payload, headers=self.headers)

        soup = bs4.BeautifulSoup(page.text, "lxml")
        return soup

    def insert_all_to_db(self):
        page_count = self.find_last_page()
        for page_num in range(page_count):
            self.insert_to_db(self.db.maintable_name, page_num)

    def find_last_page(self):
        soup = self.get_page_soup(1)
        num = soup.find("div", class_="pagination").find_all("span", class_="page-index")[-1].text
        return int(num)

    def insert_to_db(self, tablename, page_number=1):
        print("Parsing a page...")
        soup = self.get_page_soup(page_number)
        findings = soup.find("table", class_= "problems").find_all("tr")[1:]
        for item in findings:
            row_id_raw = list(filter(lambda x: "/problemset/problem/" in x["href"], item.find_all("a", {"href":True})))
            row_topic_raw = item.find_all("a", {"class":"notice"})
            row_rating_raw = item.find_all("span", {"class":"ProblemRating"})
            row_solved_count_raw = item.find_all("a", {"title":"Количество решивших задачу"})

            row_id_raw[0] = str(row_id_raw[0].text).strip()
            row_id_raw[1] = str(row_id_raw[1].text).strip()
            row_id_raw[0] = "".join(e for e in row_id_raw[0] if (e.isalnum() or e.isspace()))
            row_id_raw[1] = "".join(e for e in row_id_raw[1] if (e.isalnum() or e.isspace()))
            row_id = row_id_raw[0] + " " + row_id_raw[1]
            if row_topic_raw != []:
                row_topic = "; ".join(list(map(lambda x: x.text, row_topic_raw)))
            else:
                row_topic = "без темы"
            if row_rating_raw != []:
                row_rating = int(row_rating_raw[0].text)
            else:
                row_rating = 0
            if row_solved_count_raw != []:
                row_solved_count = int(row_solved_count_raw[0].text.strip().replace("x", ""))
            else:
                row_solved_count = 0
            row = (row_id, row_topic, row_rating, row_solved_count)

            self.db.insert_to_table(tablename, row)
    
    def disconnect_db(self):
        self.db.cur.close()
        self.db.conn.close()

if __name__ == "__main__":
    print(__name__)
    myDB = DataBase(dbname="tasksDB", username="postgres", host="localhost", password="postgrepassword")
    myParser = TheParser(myDB)
    myParser.insert_all_to_db()
