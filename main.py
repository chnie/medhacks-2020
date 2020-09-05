from flask import Flask, render_template, make_response, jsonify, request, session, redirect, url_for

import os
import pandas as pd
import numpy as np

from BigQueryClient import BigQueryClient

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(12).hex()

#Table Names
PATIENT = "Patients"
MEDICATIONS = "Medications"
ENCOUNTERS = "Encounters"
ORGANIZATIONS = "Organizations"
PROCEDURES = "Procedures"
OBSERVATIONS = "Observations"
CONDITIONS = "Conditions"

#Database
DATABASE = "Synthea2"

#Patient columns
PATIENT_GENDER = "GENDER"
PATIENT_RACE = "RACE"
PATIENT_ID = "Id"

#Condition Columns
CONDITION_CODE = "CODE"
CONDITION_DESCRIPTION = "DESCRIPTION"
CONDITION_PATIENT = "PATIENT"
CONDITION_START = "START"
CONDITION_STOP = "STOP"

#Organization Columns
ORGANIZATION_ID = "Id"
ORGANIZATION_NAME = "NAME"

#Conditions Columns
CONDITIONS_DESCRIPTION="DESCRIPTION"

@app.route('/')
def root():
    client = BigQueryClient()
    
    gender = [row[PATIENT_GENDER] for row in client.query("SELECT DISTINCT {} FROM {}.{}".format(PATIENT_GENDER, DATABASE, PATIENT))]
    race = [row[PATIENT_RACE] for row in client.query("SELECT DISTINCT {} FROM {}.{}".format(PATIENT_RACE, DATABASE, PATIENT))]
    conditions = [(row[CONDITION_CODE],row[CONDITION_DESCRIPTION]) for row in client.query("SELECT DISTINCT {},{} from {}.{}".format(CONDITION_CODE, CONDITION_DESCRIPTION, DATABASE, CONDITIONS))]
    practices = [(row[ORGANIZATION_ID],row[ORGANIZATION_NAME]) for row in client.query("SELECT DISTINCT {},{} from {}.{}".format(ORGANIZATION_ID, ORGANIZATION_NAME, DATABASE, ORGANIZATIONS))]
    patientno = [row.count for row in client.query("SELECT COUNT(DISTINCT {}) as count FROM {}.{}".format(PATIENT_ID, DATABASE, PATIENT))][0]

    return render_template('index.html', gender=gender, race=race, conditions=conditions, practices=practices, patientno=patientno)

@app.route("/filter_patients", methods=["GET", "POST"])
def filter_patients():
    genderfilter = [x.strip for x in request.form.get("genderfilter").strip().split(",")]
    if len(genderfilter) == 1:
        genderquery = "{}.{} = '{}'".format(PATIENT,PATIENT_GENDER, genderfilter[0])
    else:
        genderquery = ""
    positiveconditions = [x.strip() for x in request.form.get("positiveconditions").strip().split(",")]
    if len(positiveconditions) > 0:

        positiveconditionsquery = "{}.{} IN (SELECT {} FROM {}.{} WHERE {} IN ({}))".format(PATIENT,PATIENT_ID, CONDITION_PATIENT,DATABASE,CONDITIONS,CONDITIONS_DESCRIPTION, ",".join(["'{}'".format(x) for x in positiveconditions]))
    else:
        positiveconditionsquery = ""
    client = BigQueryClient()
    overallquery = "SELECT {}.{} FROM {}.{}".format(PATIENT,PATIENT_ID,DATABASE,PATIENT)
    if genderquery != "" and overallquery.find("WHERE") > -1:
        overallquery += " AND " + genderquery
    elif genderquery!="" and overallquery.find("WHERE") == -1:
        overallquery += " WHERE " + genderquery
    if positiveconditionsquery != "" and overallquery.find("WHERE") > -1:
        overallquery += " AND " + positiveconditionsquery
    elif positiveconditionsquery != "" and overallquery.find("WHERE") == -1:
        overallquery += " WHERE " + positiveconditionsquery
    
    session["activeprofile"] = [row.Id for row in client.query(overallquery)]
    return redirect("/population_summary")

@app.route("/population_summary")
def population_summary():
    conditions = get_conditions()
    condition_counts = list(conditions["DESCRIPTION"].value_counts().values)
    condition_count_labels = conditions["DESCRIPTION"].value_counts().index.tolist()
    return render_template("summarypage.html", population_size=len(session["activeprofile"]), condition_counts=condition_counts, condition_labels=condition_count_labels)

@app.route("/get_current_profiles", methods=["GET"])
def get_profiles():
    return make_response(jsonify(list(session.keys())), 200)


def get_conditions():
    client = BigQueryClient()
    result = client.query("SELECT {}, {}, {}, {} FROM {}.{} WHERE {} IN ({})".format(CONDITION_PATIENT,CONDITION_DESCRIPTION, CONDITION_START, CONDITION_STOP,DATABASE,CONDITIONS,CONDITION_PATIENT,",".join(["'{}'".format(x) for x in session["activeprofile"]])))
    return pd.DataFrame([dict(zip(x.keys(),x.values())) for x in result])

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
