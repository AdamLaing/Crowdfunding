import numpy as np
import pandas as pd
import datetime
import statsmodels.formula.api as sm
from flask import Flask, render_template, request, redirect, flash
#from wtforms import Form, TextAreaField, validators, StringField, SubmitField
from bokeh.io import show, output_file
#from bokeh.palettes import Spectral6
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.transform import factor_cmap
from bokeh.plotting import figure
import re
from bs4 import BeautifulSoup
import requests
import json
from pathlib import Path
import lxml

kick = pd.read_csv("files/Kickstarter.csv")
for i in np.arange(1,10):
    kick = pd.concat([kick, pd.read_csv("files/Kickstarter00{}.csv".format(
        i))])
for i in np.arange(10,49):
    kick = pd.concat([kick, pd.read_csv("files/Kickstarter0{}.csv".format(
        i))])

#parse the scraped category URL to find the main and sub categories
cats = kick["category"]
cat_split = cats.str.split("slug", expand=True)[1]
cat_split = cat_split.str.split('"', expand=True)[2]
cat_split = cat_split.str.split("\\", expand=True)[0]
kick['main'] = cat_split.str.split("/", expand=True)[0]
kick['sub'] = cat_split.str.split("/", expand=True)[1]

#pull out the data we care about
kdat = kick[["country", "id", "main", "sub", "staff_pick", "backers_count",
             "converted_pledged_amount", "goal", "launched_at", "deadline",
             "usd_pledged", "state"]]


#kdat.staff_pick[kdat.staff_pick == "false"] = False
#kdat.staff_pick[kdat.staff_pick == "true"] = True

#clean some columns
kdat["launch_year"] = kdat.launched_at.apply(
    datetime.datetime.fromtimestamp).dt.year
kdat["launch_month"] = kdat.launched_at.apply(
    datetime.datetime.fromtimestamp).dt.month
kdat["end_year"] = kdat.deadline.apply(
    datetime.datetime.fromtimestamp).dt.year
kdat["end_month"] = kdat.deadline.apply(
    datetime.datetime.fromtimestamp).dt.month
kdat["duration"] = (kdat.deadline.apply(datetime.datetime.fromtimestamp) -
                    kdat.launched_at.apply(
                        datetime.datetime.fromtimestamp)).dt.days

project_url = re.compile(r'.*?project":"([^"]*)"')
urls = kick['urls']
urls = pd.Series(project_url.match(url).groups()[0] for url in urls)
uniq_urls = urls.unique()

pledge_folder = Path('E:/Adam/Dropbox/Documents/DataIncubator/DataIncubator'
                     '/Project/Crowdfunding/Scrapes/pledges/')

desc_folder = Path('E:/Adam/Dropbox/Documents/DataIncubator/DataIncubator'
                     '/Project/Crowdfunding/Scrapes/descriptions')


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
#for n in list(range(889)):
for n in list(range(445, 889)):
    try:
        pledges[n] = unpickle_soup('pledges', pledge_folder, n+1)
        description[n] = unpickle_soup('description', desc_folder, n+1)
    except FileNotFoundError:
        for m in list(range(200*n, min(200*(n+1), len(uniq_urls)))):
            scrape_page(uniq_urls[m], n)
        pickle_soup('pledges', pledges[n], pledge_folder, n+1)
        pickle_soup('description', description[n], desc_folder, n+1)

