import numpy as np
import pandas as pd
import datetime
# import statsmodels.formula.api as sm
# from flask import Flask, render_template, request, redirect, flash
# from wtforms import Form, TextAreaField, validators, StringField, SubmitField
# from bokeh.io import show, output_file
# from bokeh.palettes import Spectral6
# from bokeh.models import ColumnDataSource, FactorRange
# from bokeh.transform import factor_cmap
# from bokeh.plotting import figure
import re
from bs4 import BeautifulSoup
import requests
import json
from pathlib import Path
import lxml

# kick = pd.read_csv("files/Kickstarter.csv")
# for i in np.arange(1, 10):
#     kick = pd.concat([kick, pd.read_csv("files/Kickstarter00{}.csv".format(
#         i))])
# for i in np.arange(10, 49):
#     kick = pd.concat([kick, pd.read_csv("files/Kickstarter0{}.csv".format(
#         i))])
#
# # parse the scraped category URL to find the main and sub categories
# cats = kick["category"]
# cat_split = cats.str.split("slug", expand=True)[1]
# cat_split = cat_split.str.split('"', expand=True)[2]
# cat_split = cat_split.str.split("\\", expand=True)[0]
# kick['main'] = cat_split.str.split("/", expand=True)[0]
# kick['sub'] = cat_split.str.split("/", expand=True)[1]
#
# # pull out the data we care about
# kdat = kick[["country", "id", "main", "sub", "staff_pick", "backers_count",
#              "converted_pledged_amount", "goal", "launched_at", "deadline",
#              "usd_pledged", "state"]]
#
#
# # kdat.staff_pick[kdat.staff_pick == "false"] = False
# # kdat.staff_pick[kdat.staff_pick == "true"] = True
#
# # clean some columns
# kdat["launch_year"] = kdat.launched_at.apply(
#     datetime.datetime.fromtimestamp).dt.year
# kdat["launch_month"] = kdat.launched_at.apply(
#     datetime.datetime.fromtimestamp).dt.month
# kdat["end_year"] = kdat.deadline.apply(
#     datetime.datetime.fromtimestamp).dt.year
# kdat["end_month"] = kdat.deadline.apply(
#     datetime.datetime.fromtimestamp).dt.month
# kdat["duration"] = (kdat.deadline.apply(datetime.datetime.fromtimestamp) -
#                     kdat.launched_at.apply(
#                         datetime.datetime.fromtimestamp)).dt.days
#
# project_url = re.compile(r'.*?project":"([^"]*)"')
# urls = kick['urls']
# urls = pd.Series(project_url.match(url).groups()[0] for url in urls)
# uniq_urls = urls.unique()

pledge_folder = Path('C:/Users/adaml/Dropbox/Documents/DataIncubator/DataIncubator'
                     '/Project/Crowdfunding/Scrapes/pledges/')

desc_folder = Path('C:/Users/adaml/Dropbox/Documents/DataIncubator/DataIncubator'
                   '/Project/Crowdfunding/Scrapes/descriptions/')


def pickle_soup(f, ob, path, num):
    with open(path/(f + str(num) + '.json'), 'w', encoding='utf-8') as \
            writeJSON:
        json.dump(ob, writeJSON, ensure_ascii=False)
    pass


def unpickle_soup(f, path, num):
    with open(path/(f + str(num) + '.json'), 'r', encoding='utf-8') as \
            readJSON:
        ob = json.load(readJSON)
    return ob


def scrape_page(url, n):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "lxml")  # .encode("utf-8")
    pledges[n][url] = str(soup.findAll('div', class_="pledge__info"))
    description[n][url] = str(soup.findAll('div',
                                           class_="col col-8 "
                                                  "description-container"))


pledges = [dict() for x in list(range(889))]
description = [dict() for x in list(range(889))]
for n in list(range(889)):
    try:
        pledges[n] = unpickle_soup('pledges', pledge_folder, n+1)
        description[n] = unpickle_soup('description', desc_folder, n+1)
    except FileNotFoundError:
        for m in list(range(200*n, min(200*(n+1), len(uniq_urls)))):
            scrape_page(uniq_urls[m], n)
        pickle_soup('pledges', pledges[n], pledge_folder, n+1)
        pickle_soup('description', description[n], desc_folder, n+1)


def clean_nums(pledge):
    if ',' in pledge:
        pledge = pledge.replace(',', '')
    if '$' in pledge:
        pledge = pledge.replace('$', '')
    if 'US' in pledge:
        pledge = pledge.replace('US', '')
    if '\n' in pledge:
        pledge = pledge.replace('\n', '')
    if 'backers' in pledge:
        pledge = pledge.replace('backers', '')
    if 'backer' in pledge:
        pledge = pledge.replace('backer', '')
    # print(pledge)
    return int(pledge.strip())


########################################
# SELECT BY KEY, VALUE TO RETAIN ORDER #
########################################
test_pledges = pledges[:5]
pledge_values = [(key, BeautifulSoup(campaign, 'lxml').select('."money"')) for pledge_dump in test_pledges
                 for key, campaign in pledge_dump.items()]

pledge_amounts = {}
for key, campaign in pledge_values:
    pledge_amounts[key] = [clean_nums(pledge_.get_text()) for pledge_ in campaign]

pledge_rewards_val = [(key, BeautifulSoup(campaign, 'lxml').select('.pledge__reward-description'))
                  for pledge_dump in test_pledges for key, campaign in pledge_dump.items()]
pledge_rewards = {}
for key, campaign in pledge_rewards_val:
    pledge_rewards[key] = [pledge_.get_text().replace('\n', ' ').strip().replace('  Less', '') for pledge_ in campaign]

pledge_backers_val = [(key, BeautifulSoup(campaign, 'lxml').select('."pledge__backer-count"'))
                  for pledge_dump in test_pledges for key, campaign in pledge_dump.items()]
pledge_backers = {}
for key, campaign in pledge_backers_val:
    pledge_backers[key] = [clean_nums(pledge_.get_text()) for pledge_ in campaign]

pledge_combined = {}
for key, _ in pledge_values:
    pledge_combined[key] = {'amount': pledge_amounts[key], 'backers': pledge_backers[key],
                            'rewards': pledge_rewards[key]}

test_desc = description[:5]
desc_vals = [(key, BeautifulSoup(value, 'lxml').select('p')) for desc_dump in test_desc
             for key, value in desc_dump.items()]
desc_paras = {}
for key, campaign in desc_vals:
    desc_paras[key] = [paragraph.get_text().replace(u'\xa0', ' ').replace('\n', '').strip() for paragraph in campaign]
assert(False not in [item[0] == '[' for item in desc_paras.values()])
assert(False not in [item[-1] == 'Questions about this project? Check out the FAQ' for item in desc_paras.values()])
for key, value in desc_paras.items():
    desc_paras[key] = value[1:-1]
