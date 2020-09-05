from flask import Flask, render_template, make_response, jsonify, request, session, redirect, url_for

import os
import pandas as pd
import numpy as np
from datetime import datetime

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
PATIENT_BIRTHDATE="BIRTHDATE"
PATIENT_DEATHDATE="DEATHDATE"
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
    genderfilter = list(filter(lambda x : x, [x.strip for x in request.form.get("genderfilter").strip().split(",")]))
    if len(genderfilter) == 1:
        genderquery = "{}.{} = '{}'".format(PATIENT,PATIENT_GENDER, genderfilter[0])
    else:
        genderquery = ""
    positiveconditions = list(filter(lambda x : x, [x.strip() for x in request.form.get("positiveconditions").strip().split(",")]))
    if len(positiveconditions) > 0:
        positiveconditionsquery = "{}.{} IN (SELECT {} FROM {}.{} WHERE {} IN ({}))".format(PATIENT,PATIENT_ID, CONDITION_PATIENT,DATABASE,CONDITIONS,CONDITIONS_DESCRIPTION, ",".join(["'{}'".format(x) for x in positiveconditions]))
    else:
        positiveconditionsquery = ""
    negativeconditions = list(filter(lambda x : x, [x.strip() for x in request.form.get("negativeconditions").strip().split(",")]))
    if len(negativeconditions) > 0:
        negativeconditionsquery = "{}.{} NOT IN (SELECT {} FROM {}.{} WHERE {} IN ({}))".format(PATIENT,PATIENT_ID, CONDITION_PATIENT,DATABASE,CONDITIONS,CONDITIONS_DESCRIPTION, ",".join(["'{}'".format(x) for x in positiveconditions]))
    else:
        negativeconditionsquery = ""
    upperagefilter = request.form.get("upperage").strip()
    if upperagefilter != "":
        upperagequery = "DATE_DIFF(CURRENT_DATE,{}.{},YEAR) <= {}".format(PATIENT,PATIENT_BIRTHDATE,upperagefilter)
    else:
        upperagequery = ""
    loweragefilter = request.form.get("lowerage").strip()
    if loweragefilter != "":
        loweragequery = "DATE_DIFF(CURRENT_DATE,{}.{},YEAR) >= {}".format(PATIENT,PATIENT_BIRTHDATE,loweragefilter)
    else:
        loweragequery = ""
    
    client = BigQueryClient()
    overallquery = "SELECT {}.{} FROM {}.{} WHERE {} IS NULL".format(PATIENT,PATIENT_ID,DATABASE,PATIENT,PATIENT_DEATHDATE)
    if genderquery != "" and overallquery.find("WHERE") > -1:
        overallquery += " AND " + genderquery
    elif genderquery!="" and overallquery.find("WHERE") == -1:
        overallquery += " WHERE " + genderquery
    if positiveconditionsquery != "" and overallquery.find("WHERE") > -1:
        overallquery += " AND " + positiveconditionsquery
    elif positiveconditionsquery != "" and overallquery.find("WHERE") == -1:
        overallquery += " WHERE " + positiveconditionsquery
    if negativeconditionsquery != "" and overallquery.find("WHERE") > -1:
        overallquery += " AND " + negativeconditionsquery
    elif negativeconditionsquery != "" and overallquery.find("WHERE") == -1:
        overallquery += " WHERE " + negativeconditionsquery
    if loweragequery != "" and overallquery.find("WHERE") > -1:
        overallquery += " AND " + loweragequery
    elif loweragequery != "" and overallquery.find("WHERE") == -1:
        overallquery += " WHERE " + loweragequery
    if upperagequery != "" and overallquery.find("WHERE") > -1:
        overallquery += " AND " + upperagequery
    elif upperagequery != "" and overallquery.find("WHERE") == -1:
        overallquery += " WHERE " + upperagequery
    print(request.form)
    print(overallquery)
    session["activeprofile"] = [row.Id for row in client.query(overallquery)]
    if len(session["activeprofile"]) == 0:
        return make_response("Sorry no patients found meeting that criteria", 200)
    else:
        return redirect("/population_summary")

@app.route("/population_summary")
def population_summary():
    conditions = get_conditions();
    condition_counts = conditions["DESCRIPTION"].value_counts().values
    condition_count_labels = conditions["DESCRIPTION"].value_counts().index
    condition_counts = list(condition_counts[condition_count_labels != ""])
    active_condition_counts = conditions.loc[conditions["STOP"].isnull()]["DESCRIPTION"].value_counts().values
    active_condition_count_labels = conditions.loc[conditions["STOP"].isnull()]["DESCRIPTION"].value_counts().index
    active_condition_counts = list(active_condition_counts[active_condition_count_labels != ""])
    
    unresolved = conditions.loc[conditions["STOP"].isnull()]
    unresolved = unresolved.loc[~conditions["DESCRIPTION"].isnull()]
    conditions_per_patient = list(unresolved["PATIENT"].value_counts().value_counts().values)
    conditions_per_patient_labels = unresolved["PATIENT"].value_counts().value_counts().index.tolist()
    
    #co_occurence = np.zeros((len(active_condition_count_labels),len(active_condition_count_labels)))
    #for i in range(len(active_condition_count_labels)):
    #    unresolved["DESCRIPTION"] == active_condition_count_labels[i]
    
    demographics = get_demographics()
    gender_ratio = list(demographics["GENDER"].value_counts().values)
    gender_ratio_labels  = demographics["GENDER"].value_counts().index.tolist()
    
    ages = list(demographics["AGE"].values)
    
    races = list(demographics["RACE"].value_counts().values)
    races_labels = demographics["RACE"].value_counts().index.tolist()
    
    medications = get_medications();
    active_medications_counts = medications.loc[medications["STOP"].isnull()]["DESCRIPTION"].value_counts().values
    active_medications_count_labels = medications.loc[medications["STOP"].isnull()]["DESCRIPTION"].value_counts().index
    active_medications_counts = list(active_medications_counts[active_medications_count_labels != ""])
    unresolved = medications.loc[medications["STOP"].isnull()]
    unresolved = unresolved.loc[~medications["DESCRIPTION"].isnull()]
    medications_per_patient = list(unresolved["PATIENT"].value_counts().value_counts().values)
    medications_per_patient_labels = unresolved["PATIENT"].value_counts().value_counts().index.tolist()
    
    encounters = get_encounters()
    overallencounters = [datetime.fromtimestamp(int(x) // 1000000000).strftime('%Y-%m-%d %H:%M:%S') for x in list(encounters["START"].values)]
    emergency  = [datetime.fromtimestamp(int(x) // 1000000000).strftime('%Y-%m-%d %H:%M:%S') for x in list(encounters.loc[encounters["ENCOUNTERCLASS"]=="emergency"]["START"].values)]
    outpatient  = [datetime.fromtimestamp(int(x) // 1000000000).strftime('%Y-%m-%d %H:%M:%S') for x in list(encounters.loc[encounters["ENCOUNTERCLASS"]=="outpatient"]["START"].values)]
    ambulatory  = [datetime.fromtimestamp(int(x) // 1000000000).strftime('%Y-%m-%d %H:%M:%S') for x in list(encounters.loc[encounters["ENCOUNTERCLASS"]=="ambulatory"]["START"].values)]
    encounters_per_patient = list(encounters["PATIENT"].value_counts().value_counts().values)
    encounters_per_patient_label = encounters_per_patient = encounters["PATIENT"].value_counts().value_counts().index.tolist()
    
    return render_template("summarypage.html", population_size=len(session["activeprofile"]), 
                           condition_counts=condition_counts, condition_labels=condition_count_labels.tolist(),
                           active_condition_counts=active_condition_counts, active_condition_count_labels=active_condition_count_labels.tolist(),
                           conditions_per_patient=conditions_per_patient, conditions_per_patient_labels=conditions_per_patient_labels,
                           ages=ages,gender_ratio=gender_ratio,gender_ratio_labels=gender_ratio_labels,
                           races=races, races_labels=races_labels,
                           active_medications_counts=active_medications_counts,
                           active_medications_count_labels=active_medications_count_labels.tolist(),
                           medications_per_patient=medications_per_patient,
                           medications_per_patient_labels=medications_per_patient_labels,
                           overallencounters=overallencounters, emergency=emergency,
                           outpatient=outpatient,ambulatory=ambulatory,
                           encounters_per_patient=encounters_per_patient,
                           encounters_per_patient_label=encounters_per_patient_label)

@app.route("/get_current_profiles", methods=["GET"])
def get_profiles():
    return make_response(jsonify(list(session.keys())), 200)

def get_conditions(no_profile=False):
    if no_profile == True:
        return
    else:
        client = BigQueryClient()
        result = client.query("SELECT {}, {}, {}, {} FROM {}.{} WHERE {} IN ({})".format(CONDITION_PATIENT,CONDITION_DESCRIPTION, CONDITION_START, CONDITION_STOP,DATABASE,CONDITIONS,CONDITION_PATIENT,",".join(["'{}'".format(x) for x in session["activeprofile"]])))
        return pd.DataFrame([dict(zip(x.keys(),x.values())) for x in result])

def get_demographics(no_profile=False):
    client = BigQueryClient()
    result = client.query("SELECT {}, {}, DATE_DIFF(CURRENT_DATE, {}, YEAR) as AGE, {} FROM {}.{} WHERE {} IN ({})".format(PATIENT_GENDER,PATIENT_RACE,PATIENT_BIRTHDATE,PATIENT_DEATHDATE, DATABASE, PATIENT, PATIENT_ID, ",".join(["'{}'".format(x) for x in session["activeprofile"]])))
    return pd.DataFrame([dict(zip(x.keys(),x.values())) for x in result])

def get_medications():
    client = BigQueryClient()
    result = client.query("SELECT PATIENT, START, STOP, DESCRIPTION, ENCOUNTER, REASONDESCRIPTION FROM Synthea2.Medications WHERE PATIENT IN ({})".format(",".join(["'{}'".format(x) for x in session["activeprofile"]])))
    return pd.DataFrame([dict(zip(x.keys(),x.values())) for x in result])

def get_encounters():
    client = BigQueryClient()
    result = client.query("SELECT PATIENT, START, STOP, ORGANIZATION, ENCOUNTERCLASS FROM Synthea2.Encounters WHERE PATIENT IN ({}) AND DATE_DIFF(CURRENT_DATE, CAST(START as DATE), YEAR) <= 1".format(",".join(["'{}'".format(x) for x in session["activeprofile"]])))
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
