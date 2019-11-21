import requests
from requests.auth import HTTPBasicAuth
import urllib.request
import time
import json
import re
import pandas as pd
from bs4 import BeautifulSoup

class WasedaScraper :
    def __init__(self) :
        self.HOME_URL = "https://www.wsl.waseda.jp/syllabus/JAA101.php?pLng=en"
        self.COURSE_BASE_URL = "https://www.wsl.waseda.jp/syllabus/JAA104.php?pLng=en"

        self.course_df = pd.DataFrame()
        self.course_df.to_csv("course_list.csv")

    def get_last_page(self, soup_first_page_a_tags) :
        n_tags = len(soup_first_page_a_tags)
        assert soup_first_page_a_tags[n_tags - 4].string == "Next>"
        return int(soup_first_page_a_tags[n_tags-5].string)

    def set_params(self, per_page, init_page_number, payload) :
        self.PER_PAGE = per_page
        self.INIT_PAGE_NUM = init_page_number
        self.payload = payload

    def set_boundaries(self, soup_first_page) :
        self.LAST_PAGE_NUM = self.get_last_page(soup_first_page.findAll("a"))
        self.NUM_COURSES_QUERIED = int(re.findall("\d+", soup_first_page.findAll(class_="c-selectall")[0].div.p.font.string[9:])[0])
        print("Scraping ", self.NUM_COURSES_QUERIED, " courses with ", self.LAST_PAGE_NUM, " pages...")

    def scrape_all(self, per_page, init_page_number, payload) :
        self.set_params(per_page, init_page_number, payload)
        
        soup_first_page = self.soupify_post(self.HOME_URL, self.payload)

        self.set_boundaries(soup_first_page)
        
        # Scrape pages...
        soup_current_tag_page = soup_first_page.findAll("a")
        for i in range(1, self.LAST_PAGE_NUM) :
            print("Going to page ", i)
            self.scrape_page(soup_current_tag_page, self.PER_PAGE)
        
            #next_page_number = next_tag_page(soup_current_tag_page)
            #assert type(self.next_page_number) is int
            
            next_page_number = i + 1
            self.payload["p_page"] = next_page_number
            soup_current_tag_page = self.soupify_post(self.HOME_URL, self.payload).findAll("a")

        # Handle scraping for last page
        num_courses_in_last_page = self.PER_PAGE if self.NUM_COURSES_QUERIED % self.PER_PAGE == 0 else self.NUM_COURSES_QUERIED % self.PER_PAGE
        print("Going to page ", self.LAST_PAGE_NUM)
        self.scrape_page(soup_current_tag_page, num_courses_in_last_page)
        
    def scrape_page(self, soup_tag_page, num_courses) :
        """
        Pass one entire page of courses (A list of BeautifulSoup <a> tag objects)
        Also pass the number of course hyperlinks in the page
        """
        list_course_tags = soup_tag_page[6:6+num_courses]
        assert len(list_course_tags) == num_courses

        for i in range(0, num_courses) :
            course_key = list_course_tags[i]["onclick"][32:60]
            self.scrape_course(course_key)

        # Append one page of courses to disk
        current_course_df = pd.read_csv("course_list.csv", index_col=0)
        pd.concat([current_course_df, self.course_df]).reset_index(drop=True).to_csv("course_list.csv")
        self.course_df = pd.DataFrame()

    def scrape_course(self, course_key) :
        """
        Pass a course page
        Scraped course is appended to a global list variable
        """
        
        course_page_url = self.COURSE_BASE_URL + "&pKey=" + course_key
        
        soup_course_page = self.soupify_get(url=course_page_url)
        #print(soup_course_page.findAll(class_="ct-sirabasu"))
        #print(len(soup_course_page.findAll(class_="ct-sirabasu")))

        data = self.scrape_course_info(soup_course_page)
        data["syllabus_urls"] = [course_page_url]
        
        self.course_df = self.course_df.append(data, ignore_index=True)

    def scrape_course_info(self, soup_course_page) :
        course_info = soup_course_page.findAll(class_="ct-sirabasu")[0].tbody.findAll("tr")
        syllabus_info = soup_course_page.findAll(class_="ct-sirabasu")[1].tbody.findAll("tr")
        data = {}
        
        data["year"] = course_info[0].findAll("td")[0].string[0:4]
        data["school"] = course_info[0].findAll("td")[1].string
        data["title"] = "".join([str for str in course_info[1].td.div.strings]).replace("\n", " ")
        data["instructors"] = []
        # data["term_day_period"] = course_info[3].td.string
        data["category"] = course_info[4].findAll("td")[0].string
        data["eligible_year"] = course_info[4].findAll("td")[1].string
        data["credits"] = int(course_info[4].findAll("td")[2].string)
        #data["classroom"] = course_info[5].findAll("td")[0].string
        data["campus"] = course_info[5].findAll("td")[1].string
        data["course_class_code"] = course_info[6].findAll("td")[1].string
        data["main_language"] = course_info[7].td.string
        data["course_code"] = course_info[8].td.string
        data["academic_disciplines"] = [course_info[9].td.string, course_info[10].td.string, course_info[11].td.string] # first, second, third
        data["level"] = course_info[12].findAll("td")[0].string
        # data["type"] = course_info[12].findAll("td")[1].string
        
        # data["subtitle"] = syllabus_info[0].td.strings
        # data["outline"] = syllabus_info[1].td.strings
        # data["objectives"] = syllabus_info[2].td.strings
        # data["before_after_study"] = syllabus_info[3].td.strings
        # data["schedule"] = syllabus_info[4].td.strings
        # data["textbooks"] = syllabus_info[6].td.strings
        # data["references"] = syllabus_info[7].td.strings
            
        instructors = course_info[2].td.string
        if "\uff0f" in instructors :
            for instructor in instructors.split("\uff0f") :
                data["instructors"].append(instructor)
        else :
            data["instructors"].append(instructors)
                    
        data["term"] = course_info[3].td.string.split("\u00a0\u00a0")[0]
        days_periods = course_info[3].td.string.split("\u00a0\u00a0")[1]
        classrooms = [course_info[5].findAll("td")[0].string]
        classrooms = classrooms[0].split("\uff0f") if "\uff0f" in classrooms[0] else classrooms
        data["sessions"] = []
        if "\uff0f" in days_periods : # Multiple sessions
            #assert len(classrooms) > 1
            for day_period in days_periods.split("\uff0f") :
                session = {"day": self.split_day_period(day_period)[0][3:], "period": self.split_day_period(day_period)[1], "classrooms": []}
                for classroom in classrooms :
                    if self.split_day_period(day_period)[0][0:3] in classroom :
                        session["classrooms"].append(classroom[3:])
                    elif len(classrooms) == 1 :
                        session["classrooms"].append(classroom)
                data["sessions"].append(session)

        else : # One session
            #assert len(classrooms) == 1
            session = {"day": self.split_day_period(days_periods)[0], "period": self.split_day_period(days_periods)[1], "classrooms": []}
            if len(classrooms) > 1 :
                for classroom in classrooms :
                    session["classrooms"].append(classroom)
            else :
                session["classrooms"].append(classrooms[0])
            data["sessions"].append(session)

        return data

    def soupify_get(self, url) :
        #time.sleep(0.1)
        response = requests.get(url=url)
        return BeautifulSoup(response.text, "html.parser")

    def soupify_post(self, url, payload) :
        #time.sleep(0.1)
        response = requests.post(url=url, data=payload)
        return BeautifulSoup(response.text, "html.parser")

    def split_day_period(self, day_period) :
        if "." in day_period :
            res = day_period.split(".")
        else :
            res = [day_period, ""]
        return res
    

#########################
## Scraper starts here ##
#########################

# Set up macro, syllabus url, and post parameters
PER_PAGE = 100 # 10, 20, 50, or 100
PAGE_INIT = 1

payload = {"keyword": "",
           "p_number": PER_PAGE,
           "p_page": PAGE_INIT,
           "s_bunya1_hid": "Please select the First Academic disciplines.",
           "s_bunya2_hid": "Please select the Second Academic disciplines.",
           "s_bunya3_hid": "Please select the Third Academic disciplines.",
           "p_gakki": "",
           "pfrontPage": "now",
           "p_jigen": "",
           "p_gengo": "02",
           "p_gakubu": "",
           "p_keya": "",
           "p_searcha": "",
           "p_searchb": "",
           "pClsOpnSts": 123,
           "ControllerParameters": "JAA103SubCon",
           "pLng": "en",
           }

w = WasedaScraper()
w.scrape_all(PER_PAGE, PAGE_INIT, payload)
