import requests
from requests.auth import HTTPBasicAuth
import urllib.request
import time
import json
from bs4 import BeautifulSoup

def soupify_get(url) :
    time.sleep(1)
    response = requests.get(url=url)
    return BeautifulSoup(response.text, "html.parser")

def soupify_post(url, payload) :
    time.sleep(1)
    response = requests.post(url=url, data=payload)
    return BeautifulSoup(response.text, "html.parser")

def get_last_page(soup_first_page_a_tags, per_page) :
    n_tags = len(soup_first_page_a_tags)
    assert soup_first_page_a_tags[n_tags - 4].string == "Next>"
    
    return int(soup_first_page_a_tags[n_tags-5].string)

def add_to_json(data) :
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

def scrape_course(course_key) :
    course_page_base_url = "https://www.wsl.waseda.jp/syllabus/JAA104.php?pLng=en"
    course_page_url = course_page_base_url + "&pKey=" + course_key
    
    soup_course_page = soupify_get(url=course_page_url)
    #print(soup_course_page.findAll(class_="ct-sirabasu"))
    #print(len(soup_course_page.findAll(class_="ct-sirabasu")))
    course_info = soup_course_page.findAll(class_="ct-sirabasu")[0].tbody.findAll("tr")
    syllabus_info = soup_course_page.findAll(class_="ct-sirabasu")[1].tbody.findAll("tr")

    data = {}
    data["syllabus_url"] = course_page_url
    data["year"] = course_info[0].findAll("td")[0].string
    data["school"] = course_info[0].findAll("td")[1].string
    data["title"] = course_info[1].td.div.string
    data["instructor"] = course_info[2].td.string
    data["term_day_period"] = course_info[3].td.string
    data["category"] = course_info[4].findAll("td")[0].string
    data["eligible_year"] = course_info[4].findAll("td")[1].string
    data["credits"] = int(course_info[4].findAll("td")[2].string)
    data["classroom"] = course_info[5].findAll("td")[0].string
    data["campus"] = course_info[5].findAll("td")[1].string
    data["course_class_code"] = course_info[6].findAll("td")[1].string
    data["main_language"] = course_info[7].td.string
    data["course_code"] = course_info[8].td.string
    data["first_academic_disciplines"] = course_info[9].td.string
    data["second_academic_disciplines"] = course_info[10].td.string
    data["third_academic_disciplines"] = course_info[11].td.string
    data["level"] = course_info[12].findAll("td")[0].string
    #data["type"] = course_info[12].findAll("td")[1].string

    # data["subtitle"] = syllabus_info[0].td.strings
    # data["outline"] = syllabus_info[1].td.strings
    # data["objectives"] = syllabus_info[2].td.strings
    # data["before_after_study"] = syllabus_info[3].td.strings
    # data["schedule"] = syllabus_info[4].td.strings
    # data["textbooks"] = syllabus_info[6].td.strings
    # data["references"] = syllabus_info[7].td.strings

    add_to_json(data) # Write to a local file
    
    #print(requests.post(url="https://api.ratemywaseda.com/courses/", data=json.dumps(data), auth=HTTPBasicAuth("admin2", "password1"), headers={"content-type": "application/json"})) # post to api, debug
    
def scrape_page(soup_tag_page, per_page) :
    list_course_tags = soup_tag_page[6:6+per_page]
    assert len(list_course_tags) == per_page
    
    for i in range(0, per_page) :
        course_key = list_course_tags[i]["onclick"][32:60]
        scrape_course(course_key)

def next_tag_page(soup_tag_page) :
    n_tags = len(soup_tag_page)
    assert soup_tag_page[n_tags - 4].string == "Next>"
    #next_page_number = int(soup_tag_page[n_tags-4]["onclick"][29])
    return int(soup_tag_page[n_tags-4]["onclick"][29])


PER_PAGE = 10 # 10, 20, 50, or 100
PAGE_INIT = 1
home_url="https://www.wsl.waseda.jp/syllabus/JAA101.php?pLng=en"
instance_base_url = "https://www.wsl.waseda.jp/syllabus/JAA104.php?pLng=en"
#course_key_set = (,)

payload = {"keyword": "signal processing",
           "p_number": PER_PAGE,
           "p_page": PAGE_INIT,
           "s_bunya1_hid": "Please select the First Academic disciplines.",
           "s_bunya2_hid": "Please select the First Academic disciplines.",
           "s_bunya3_hid": "Please select the First Academic disciplines.",
           "p_gakki": "",
           "pfrontPage": "now",
           "p_gengo": "02",
           "p_gakubu": 262006,
           "p_searcha": "a",
           "p_searchb": "b",
           "pClsOpnSts": 123,
           "ControllerParameters": "JAA103SubCon",
           "pLng": "en",
           }

soup_first_page = soupify_post(home_url, payload)
last_page_number = get_last_page(soup_first_page.findAll("a"), PER_PAGE)

soup_current_tag_page = soup_first_page.findAll("a")
for i in range(1, last_page_number) :
    scrape_page(soup_current_tag_page, PER_PAGE)
    
    next_page_number = next_tag_page(soup_current_tag_page)
    payload["p_page"] = next_page_number
    soup_current_tag_page = soupify_post(home_url, payload).findAll("a")

#TODO: scrape last page after the loop

