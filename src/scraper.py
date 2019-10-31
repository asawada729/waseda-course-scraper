import requests
from requests.auth import HTTPBasicAuth
import urllib.request
import time
import json
import re
import pandas as pd
from bs4 import BeautifulSoup

def soupify_get(url) :
    #time.sleep(0.1)
    response = requests.get(url=url)
    return BeautifulSoup(response.text, "html.parser")

def soupify_post(url, payload) :
    #time.sleep(0.1)
    response = requests.post(url=url, data=payload)
    return BeautifulSoup(response.text, "html.parser")

def get_last_page(soup_first_page_a_tags, per_page) :
    n_tags = len(soup_first_page_a_tags)
    assert soup_first_page_a_tags[n_tags - 4].string == "Next>"
    
    return int(soup_first_page_a_tags[n_tags-5].string)

def add_to_json(data) :
    """
    Write one course data to a json file
    Slow, becuase this code extracts the exising contents of the json file -> appends the new course in runtime -> deletes contents in json file -> writes the existing contents+apended new course
    
    Note that we don't handle duplicate data when writing to json file.
    """
    with open("course_data.json", "a+") as json_file :
        json_file.seek(0)
        try:
            current_data = json.load(json_file)
        except json.decoder.JSONDecodeError :
            current_data = {"course_list" : []}
        finally :
            assert type(current_data["course_list"]) is list
            current_data["course_list"].append(data)
            json_file.truncate(0)
            json.dump(current_data, json_file)
            
def add_to_df(data) :
    global df
    df = df.append(data, ignore_index=True)

def split_day_period(day_period) :
    if "." in day_period :
        res = day_period.split(".")
    else :
        res = [day_period, ""]
    return res

def scrape_course(course_key) :
    """
    Pass a course page
    Scraped course is appended to a global list variable
    """
    #global course_data_list
    course_page_base_url = "https://www.wsl.waseda.jp/syllabus/JAA104.php?pLng=en"
    course_page_url = course_page_base_url + "&pKey=" + course_key
    
    soup_course_page = soupify_get(url=course_page_url)
    #print(soup_course_page.findAll(class_="ct-sirabasu"))
    #print(len(soup_course_page.findAll(class_="ct-sirabasu")))
    course_info = soup_course_page.findAll(class_="ct-sirabasu")[0].tbody.findAll("tr")
    syllabus_info = soup_course_page.findAll(class_="ct-sirabasu")[1].tbody.findAll("tr")

    data = {}
    data["syllabus_url"] = [course_page_url]
    data["year"] = course_info[0].findAll("td")[0].string[0:4]
    data["school"] = course_info[0].findAll("td")[1].string
    data["title"] = course_info[1].td.div.string
    data["instructors"] = course_info[2].td.string
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

    # serial = data["title"] + data["course_class_code"] + data["instructors"]
    # if serial in all_serials :
    #     course_data_list[course_data_list.index(scraped_course)]["syllabus_url"].extend(data["syllabus_url"]) 
    #     return
    
    # for scraped_course in course_data_list :
    #     if course_data_list == [] :
    #         break
    #     if data["title"]==scraped_course["title"] and data["instructors"]==scraped_course["instructors"] and data["course_class_code"]==scraped_course["course_class_code"] :
    #         course_data_list[course_data_list.index(scraped_course)]["syllabus_url"].extend(data["syllabus_url"]) 
    #         return

    instructors = data["instructors"]
    data["instructors"] = []
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
    if "\uff0f" in days_periods :
        #assert len(classrooms) > 1
        for day_period in days_periods.split("\uff0f") :
            session = {"day": split_day_period(day_period)[0][3:], "period": split_day_period(day_period)[1], "classrooms": []}
            for classroom in classrooms :
                if split_day_period(day_period)[0][0:3] in classroom :
                    session["classrooms"].append(classroom[3:])
                elif len(classrooms) == 1 :
                    session["classrooms"].append(classroom)
            data["sessions"].append(session)

    else :
        #assert len(classrooms) == 1
        session = {"day": split_day_period(days_periods)[0], "period": split_day_period(days_periods)[1], "classrooms": []}
        if len(classrooms) > 1 :
            for classroom in classrooms :
                session["classrooms"].append(classroom)
        else :
            session["classrooms"].append(classrooms[0])
        data["sessions"].append(session)

    add_to_df(data)
    #add_to_json(data)
    
def scrape_page(soup_tag_page, per_page) :
    """
    Pass one entire page of courses (A list of BeautifulSoup objects)
    Also pass the number of course hyperlinks in the page
    """
    list_course_tags = soup_tag_page[6:6+per_page]
    assert len(list_course_tags) == per_page

    for i in range(0, per_page) :
        course_key = list_course_tags[i]["onclick"][32:60]
        scrape_course(course_key)

def write_to_local(all_scraped_courses) :
    num_courses = 0
    for course_data in all_scraped_courses :
        add_to_json(course_data)
        num_courses += 1
    print("Wrote ", num_courses, " courses to course_data.json.")

def post_to_api(all_scraped_courses) :
    num_courses = 0
    for course_data in all_scraped_courses :
        print(requests.post(url="https://api.ratemywaseda.com/courses/", data=json.dumps(course_data), auth=HTTPBasicAuth("admin2", "password1"), headers={"content-type": "application/json"})) # post to api, debug
        num_courses += 1
    print("Posted ", num_courses, " courses to API.")


#########################
## Scraper starts here ##
#########################

# Set up macro, syllabus url, and post parameters
PER_PAGE = 100 # 10, 20, 50, or 100
PAGE_INIT = 1
home_url="https://www.wsl.waseda.jp/syllabus/JAA101.php?pLng=en"
instance_base_url = "https://www.wsl.waseda.jp/syllabus/JAA104.php?pLng=en"
df = pd.DataFrame()

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

soup_first_page = soupify_post(home_url, payload)

# Define boundaries
last_page_number = get_last_page(soup_first_page.findAll("a"), PER_PAGE)
number_of_courses_queried = re.findall("\d+", soup_first_page.findAll(class_="c-selectall")[0].div.p.font.string[9:])[0]

print("Scraping ", number_of_courses_queried, " courses with ", last_page_number, " pages...")

# Scrape pages...
soup_current_tag_page = soup_first_page.findAll("a")
for i in range(1, last_page_number) :
    print("Going to page ", i)
    scrape_page(soup_current_tag_page, PER_PAGE)
    
    #next_page_number = next_tag_page(soup_current_tag_page)
    #assert type(next_page_number) is int

    next_page_number = i + 1
    payload["p_page"] = next_page_number
    soup_current_tag_page = soupify_post(home_url, payload).findAll("a")

# Handle scraping for last page
num_courses_last_page = PER_PAGE if int(number_of_courses_queried) % PER_PAGE == 0 else int(number_of_courses_queried) % PER_PAGE
print("Going to page ", last_page_number)
scrape_page(soup_current_tag_page, num_courses_last_page)

# Output
df.to_csv("course_list.csv")
#write_to_local(course_data_list)
#post_to_api(course_data_list)
