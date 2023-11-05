import os
import pandas
from flask import Flask, render_template, flash, request, redirect, session, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000     #prevents uploads of huge files

app.secret_key = 'very secret!'

def check_allowed_file (filename):
    if ('.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS):
        return True
    else:
        return False

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template("home.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/showdata", methods=['GET', 'POST'])
def show_data():
    if request.method == 'POST':
        # check to make sure request is correct
        if ('csvFile' not in request.files):
            flash('incorrect request')
            return redirect (request.url)
        file = request.files['csvFile']
        # if no file submitted or has no filename
        if (file.filename == ''):
            flash('file not found')
            return redirect (request.url)
        # if file not csv
        if check_allowed_file(file.filename) == False:
            flash('wrong file type')
            return redirect (request.url)
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # allows accessing same file from other pages!
        # session['uploaded_csv_path'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # return redirect(url_for('show_data'))
        # file_path = session.get('uploaded_csv_path')
        uploaded_csv = pandas.read_csv(file_path, nrows=300)
        html_csv = uploaded_csv.to_html()
        return render_template("data.html", csv_data=html_csv)
    return render_template("data.html", csv_data="")

@app.route("/results/<filename>")
def download_results(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# for entering specific user data
@app.route("/calculator")
def calculator():
    return render_template("calculator.html")

# for viewing results
@app.route("/user_results", methods=['POST'])
def user_results():
    income = request.form['income']
    credit_card = request.form['credit_card']
    car = request.form['car']
    student_loan = request.form['student_loan']
    appraised_value = request.form['appraised_value']
    down_payment = request.form['down_payment']
    loan_amount = request.form['loan_amount']
    mortgage_payment = request.form['mortgage_payment']
    credit_score = request.form['credit_score']
    # print(income, credit_card, car, student_loan, appraised_value, down_payment, loan_amount, mortgage_payment, credit_score);
    return render_template("results.html")