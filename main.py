from flask import Flask, render_template

from BigQueryClient import BigQueryClient

app = Flask(__name__)
#Table Names
PATIENT = "Patients"
MEDICATIONS = "Medications"
ENCOUNTERS = "Encounters"
ORGANIZATIONS = "Organizations"
PROCEDURES = "Procedures"
OBSERVATIONS = "Observations"
CONDITIONS = "Conditions"

#Patient columns
PATIENT_GENDER = "GENDER"
PATIENT_RACE = "RACE"
PATIENT_ID = "Id"

#Condition Columns
CONDITION_CODE = "CODE"
CONDITION_DESCRIPTION = "DESCRIPTION"

#Organization Columns
ORGANIZATION_ID = "Id"
ORGANIZATION_NAME = "NAME"

@app.route('/')
def root():
    client = BigQueryClient()
    
    gender = [row[PATIENT_GENDER] for row in client.query("SELECT DISTINCT {} FROM Synthea2.{}".format(PATIENT_GENDER, PATIENT))]
    race = [row[PATIENT_RACE] for row in client.query("SELECT DISTINCT {} FROM Synthea2.{}".format(PATIENT_RACE, PATIENT))]
    conditions = [(row[CONDITION_CODE],row[CONDITION_DESCRIPTION]) for row in client.query("SELECT DISTINCT {},{} from Synthea2.{}".format(CONDITION_CODE, CONDITION_DESCRIPTION, CONDITIONS))]
    practices = [(row[ORGANIZATION_ID],row[ORGANIZATION_NAME]) for row in client.query("SELECT DISTINCT {},{} from Synthea2.{}".format(ORGANIZATION_ID, ORGANIZATION_NAME, ORGANIZATIONS))]
    patientno = [row.count for row in client.query("SELECT COUNT(DISTINCT {}) as count FROM Synthea2.{}".format(PATIENT_ID, PATIENT))][0]

    return render_template('index.html', gender=gender, race=race, conditions=conditions, practices=practices, patientno=patientno)

@app.route("/filter_patients")
def filter_patients():
    pass

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
