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
        file_path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
        # allows accessing same file from other pages!
        # session['uploaded_csv_path'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # return redirect(url_for('show_data'))
        # file_path = session.get('uploaded_csv_path')

        df = pandas.read_csv(file_path)
        listOfDicts = []

        for index, row in df.iterrows():
            eligibilityCheck = checkEligibility(row)
            listOfDicts.append(eligibilityCheck)

        newdf = pandas.DataFrame(listOfDicts)
        out = pandas.merge(df, newdf, on="ID").to_csv(os.path.join(app.config['UPLOAD_FOLDER'], "out.csv"), index=False)

        file_path = os.path.join(app.config['UPLOAD_FOLDER'],"out.csv")

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

    return render_template("results.html")

def checkEligibility(row):
    id = row['ID']
    income = row['GrossMonthlyIncome']
    credit_card = row['CreditCardPayment']
    car_payment = row['CarPayment']
    loan_payments = row['StudentLoanPayments']
    appraised_value = row['AppraisedValue']
    down_payment = row['DownPayment']
    loan_amount = row['LoanAmount']
    mortgage_payment = row['MonthlyMortgagePayment']
    credit_score = row['CreditScore']

    # print(income, credit_card, car, student_loan, appraised_value, down_payment, loan_amount, mortgage_payment, credit_score);
    
    loan_amount = appraised_value - down_payment
    ltv = round((loan_amount / appraised_value) * 100, ndigits = 2)
    monthlyDebt = car_payment + credit_card + mortgage_payment + loan_payments
    dti = round((monthlyDebt / income) * 100, ndigits = 2)
    fedti = round((mortgage_payment / income) * 100, ndigits = 2)

    # eligibility check
    eligibilityCheck = {
        "ID": 0,
        "CreditScore": False,
        "LTV": 0,
        "PMI": False,
        "DTV": 0,
        "FEDTI": False,
        "Approved": False
    }

    eligibilityCheck["ID"] = id

    eligibilityCheck["CreditScore"] = (credit_score > 640)
    
    if dti <= 36 and (mortgage_payment / monthlyDebt) <= 28:
        eligibilityCheck["DTV"] = 0
    elif dti >= 36 and dti <= 43:
        eligibilityCheck["DTV"] = 1
    else:   
        eligibilityCheck["DTV"] = 2

    if ltv < 80:
        eligibilityCheck["LTV"] = 0
    elif ltv >= 80 and ltv < 95:
        eligibilityCheck["LTV"] = 1
        eligibilityCheck["PMI"] = True
    else:
        eligibilityCheck["LTV"] = 2

    eligibilityCheck["FEDTI"] = fedti <= 28

    if (eligibilityCheck["CreditScore"] 
        and (eligibilityCheck["LTV"]==0 or eligibilityCheck["LTV"]==1)
        and eligibilityCheck["FEDTI"]
        and (eligibilityCheck["DTV"]==0 or eligibilityCheck["DTV"]==1)):
        eligibilityCheck["Approved"] = True
    return eligibilityCheck
