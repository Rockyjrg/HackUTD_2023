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
    income = float(request.form['income'])
    credit_card = float(request.form['credit_card'])
    car_payment = float(request.form['car'])
    student_loan = float(request.form['student_loan'])
    appraised_value = float(request.form['appraised_value'])
    down_payment = float(request.form['down_payment'])
    loan_amount = float(request.form['loan_amount'])
    mortgage_payment = float(request.form['mortgage_payment'])
    credit_score = float(request.form['credit_score'])

    loan_amount = appraised_value - down_payment
    LTV = round((loan_amount / appraised_value) * 100, ndigits = 2)
    PMI = round(mortgage_payment * 1.01, ndigits = 2)
    monthlyDebt = car_payment + credit_card + mortgage_payment + loan_amount
    DTI = round((monthlyDebt / income) * 100, ndigits = 2)
    FEDTI = round((mortgage_payment / income) * 100, ndigits = 2)

    eligibilityCheck = []

    if credit_score > 640:
        eligibilityCheck.append('Great job, it looks like you met the required Credit Score: {}'.format(credit_score))
    else:
        eligibilityCheck.append("Sorry it looks like you didn't exactly reach the required credit score of 640 since you had a {}, but that doesn't mean you should give up.\n I have some great resources for you to check out that can help you raise your scores: \n".format(credit_score))
    
    if LTV < 80:
        eligibilityCheck.append("You have a LTV of below 80, it is {}. No Need for PMI".format(LTV))
    elif LTV >= 80 and LTV < 95:
        eligibilityCheck.append("PMI required: LTV is {}%. PMI costs will apply. Your monthly payment will increase to {}".format(LTV,PMI))
    else:
        eligibilityCheck.append("Sorry, your LTV is above 95%. Your current LTV is {}. Consider increasing your down payment if you are able to, if not it isn't the end of the world. There are more ways to decrease your LTV to 80%. I have linked some articles just for you.".format(LTV))

    if DTI <= 36 and (mortgage_payment / monthlyDebt) <= 28:
        eligibilityCheck.append("Pass: Debt to income ratio is in preferred range of no more than 36%, you are at {}.".format(DTI))
    elif DTI >= 36 and DTI <= 43:
        eligibilityCheck.append("You may not be eligible for a loan with a debt to income ratio of {}.".format(DTI))
    else:   
        eligibilityCheck.append("You have a DTI rato of {}. You could try transferring loans into a low interest credit card as a way of lowering your Debt to income ratio. I have some articles you can read on how you can go about doing this".format(DTI))

    if FEDTI <= 28:
        eligibilityCheck.append("Great job, it looks like your front-end debt to income is less than or equal to 28% and is in fact {}".format(FEDTI))
    else:
        eligibilityCheck.append('Sorry to say but your front-end debt to income was not less than or equal to 28%. It was {}.\n Do not worry at all though, I have great resources on reducing your FEDTI'.format(FEDTI))


    return render_template("results.html", eligibilityCheck=eligibilityCheck)

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
