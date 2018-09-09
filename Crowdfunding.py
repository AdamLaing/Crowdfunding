import numpy as np
import pandas as pd
import datetime
import statsmodels.formula.api as sm
from flask import Flask, render_template, request, redirect, flash
from wtforms import Form, TextAreaField, validators, StringField, SubmitField

DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import components

#read in the data
indie = pd.read_csv("files/Indiegogo.csv")
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

#take residuals of converted_pledge~usd
results = sm.ols(formula='converted_pledged_amount~usd_pledged',
                  data=kdat).fit()
CPA_pred = results.predict(kdat[["usd_pledged"]])
kdat["conv_res"] = kdat["converted_pledged_amount"].values-CPA_pred



class KickstarterForm(Form):
    main = StringField('Main Category:', validators=[validators.required()])
    sub = StringField('Sub-category:', validators=[validators.required()])
    camp_dur = StringField('Campaign Duration (days):', validators=[
        validators.required()])
    launch_month = StringField('Launch Month:', validators=[
        validators.required()])
    goal = StringField('Goal Amount (USD):', validators=[
        validators.required()])


@app.route('/')
def index():
    # Index will give options of exploring Kickstarter, Indiegogo, possibly
    # other data if I find suitable APIs, and list plots and general info
    # about the datasets.
    return render_template('index.html')


@app.route('/kickstarter', methods=('GET', 'POST'))
def kickstarter():
    form = KickstarterForm(request.form)

    if request.method == 'POST':
        main = request.form['main']
        sub = request.form['sub']
        camp_dur = request.form['camp_dur']
        launch_month = request.form['launch_month']
        goal = request.form['goal']
        error = None

        if launch_month not in np.arange(1,13) and launch_month != "None":
            error = 'Please enter launch month as a number from 1 to 12, ' \
                    'or enter "None".'

        elif main not in kdat.main and main != "None":
            error = 'Invalid Main Category. Please check your spelling, ' \
                    'or enter "None".'

        elif sub not in kdat.sub and sub != "None":
            error = 'Invalid Sub-category. Please check your spelling, ' \
                    'or enter "None".'

        elif not isinstance(camp_dur, int) and camp_dur != "None":
            error = 'Invalid Campaign Duration. Please enter an integer, ' \
                    'or enter "None".'

        elif not isinstance(goal, int) and goal != "None":
            error = 'Invalid Goal Amount. Please enter an integer, ' \
                    'or enter "None".'
        if error is None:
            data = kdat
            if main != "None":
                data = data.loc[data.main == main]
            if sub != "None":
                data = data.loc[data.sub == sub]
            if camp_dur != "None":
                data = data.loc[data.duration == camp_dur]
            if launch_month != "None":
                data = data.loc[data.launch_month == launch_month]
            if goal != "None":
                data = data.loc[data.goal <= 1.1*goal and data.goal >= .9*goal]

            # Delete rows with duplicate IDs
            data = data.drop_duplicates(subset="id")

            p = figure(plot_width=400, plot_height=400, x_axis_type='datetime')

            # add a line renderer
            p.line(data['date'], data['close'], line_width=2)

            script, div = components(p)
            flash('[Placeholder Text')
            return render_template('kickstarter.html', div=div, script=script,
                                   form=form)

        flash(error)
    return render_template('kickstarter.html', form=form)


if __name__ == '__main__':
    app.run(port=33507)
