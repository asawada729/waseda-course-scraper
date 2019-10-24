import pandas as pd
import json

with open("course_data.json", "r") as json_file :
    data = json.load(json_file)

df = pd.DataFrame(data["course_list"])
df.to_csv("course_list.csv")
