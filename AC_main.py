from wtforms import TextField, Form
from BigQueryClient import BigQueryClient


app = Flask(__name__)
class SearchForm(Form):
    gendercomp = TextField('Patient Gender', id='patient_gender')
    racecomp = TextField('Patient Race', id='patient_race')


@app.route('/_autocomplete', methods=['GET'])
def autocomplete():
 #   client = BigQueryClient()
    
 #   gender = ["Male", "Female", "Other"]
    race = ["White", "Asian", "Black"]
   
#    print(gender)
    print(race)
    return Response(json.dumps(race), mimetype='application/json')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm(request.form)
    return render_template("index.html", form=form)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(debug=True)
