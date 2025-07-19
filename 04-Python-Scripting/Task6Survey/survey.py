#!/usr/bin/env python3
# This script creates a survey on surveymonkey using API.
# Install requests if not available
try:
    import requests
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

import json

# set api token and header
ACCESS_TOKEN = 'hjdhSvlz8eyDiJbFSb5.TCkiRG5bKi5RQSJKKJ7kRaIbstZxDOCTVOqqC0V.5DhX5XONXPdRUxzl5Bts9UfJJ6B-KScDMc21BQNkzlJr3DhqbLq7eQ.L-jbouzUpzT7l'
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}', 
    'Content-Type': 'application/json' 
}
with open("table.json") as f: #load survey from json file
    data = json.load(f) 

survey_title = list(data.keys())[0] # first key is the title
questions = data[survey_title]["General Questions"] 

# Create survey
res = requests.post("https://api.surveymonkey.com/v3/surveys", headers=HEADERS, json={"title": survey_title}) # post req to create survey
if res.status_code != 201:
    print("Failed to create survey:", res.status_code)
    exit()

survey_id = res.json()["id"] # get the id and print it
print("Survey created with ID:", survey_id)

# Create a page
page = requests.post(f"https://api.surveymonkey.com/v3/surveys/{survey_id}/pages", headers=HEADERS, json={"title": "Page 1"})
if page.status_code != 201:
    print("Failed to create page:", page.status_code)
    exit()

page_id = page.json()["id"]

# Add questions
for question_text, details in questions.items():
    answers = [{"text": ans} for ans in details["Answers"]]
    q = {
        "headings": [{"heading": question_text}],
        "family": "single_choice",
        "subtype": "vertical",
        "answers": {"choices": answers}
    }
    r = requests.post(f"https://api.surveymonkey.com/v3/surveys/{survey_id}/pages/{page_id}/questions", headers=HEADERS, json=q)
    print("Added:" if r.status_code == 201 else "Failed:", question_text)