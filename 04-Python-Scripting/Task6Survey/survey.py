#!/usr/bin/env python3
# script creates a survey on SurveyMonkey using the API.
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv() #load enviroment variables

# getn access token from env file
ACCESS_TOKEN = os.getenv("SURVEYMONKEY_API_KEY") #get access token from the file
if not ACCESS_TOKEN:
    raise EnvironmentError("API key not found in .env")

HEADERS = {                                     #auth header for api requests
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}
with open("table.json") as f:                   #load table from json
    data = json.load(f)

survey_title = list(data.keys())[0]           # first key is the title
questions = data[survey_title]["General Questions"]

res = requests.post("https://api.surveymonkey.com/v3/surveys", headers=HEADERS, json={"title": survey_title})
if res.status_code != 201:
    print("Failed to create survey:", res.status_code, res.text)
    exit()

survey_id = res.json()["id"]
print("Survey created with ID:", survey_id)

# create a page
page = requests.post(f"https://api.surveymonkey.com/v3/surveys/{survey_id}/pages", headers=HEADERS, json={"title": "Page 1"})
if page.status_code != 201:
    print("Failed to create page:", page.status_code, page.text)
    exit()

page_id = page.json()["id"]

# add questions to the survey
for question_text, details in questions.items():
    answers = [{"text": ans} for ans in details["Answers"]]
    question_payload = {
        "headings": [{"heading": question_text}],
        "family": "single_choice",
        "subtype": "vertical",
        "answers": {"choices": answers}
    }
    r = requests.post(
        f"https://api.surveymonkey.com/v3/surveys/{survey_id}/pages/{page_id}/questions",
        headers=HEADERS,
        json=question_payload
    )
    print("Added:" if r.status_code == 201 else "Failed:", question_text)
