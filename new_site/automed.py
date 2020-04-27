from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import Levenshtein as lev #pip install python-levenshtein

def search(drug,row):
    try:
        if drug in row:
            return True
        else:
            for word in row:
                #Levenshtein distance ratio
                ratio = lev.ratio(drug, word)
                if ratio > 0.8:
                    return True
            return False
    except:
        return False

def correct_drug_name(drug, names):
    for row in names:
        if drug in row:
            return drug
        else:
            for word in row:
                #Levenshtein distance ratio
                ratio = lev.ratio(drug, word)
                if ratio > 0.8:
                    return word
            return False


drug_data = pd.read_csv("substitutes.csv")
drug_data["Trade_Name"] = drug_data["Trade_Name"].str.lower()
drug_data["Ingredient"] = drug_data["Ingredient"].str.lower()
drug_data['Ingredient'] = drug_data['Ingredient'].str.split(';| ')
drug_data['Name'] = drug_data['Trade_Name'].str.split(';| ')

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("automed_test.html")

@app.route('/handle_data', methods=['POST','GET'])
def handle_data():
    if request.method == "POST":
        
        new_pres_drug = request.form['drug']
        new_pres_drug = new_pres_drug.lower().split(",")

        result = []
        no = []

        for drug in new_pres_drug:
            a = drug_data.apply(lambda row : search(drug,row['Ingredient']), axis = 1)
            b = drug_data.apply(lambda row : search(drug,row['Name']), axis = 1)

            substitutes = drug_data[a | b].sort_values('Price').head(5)
            n = len(substitutes)

            if n > 0 and drug:
                #find correct drug name
                drug_name = correct_drug_name(drug, substitutes['Name'])
                if not drug_name:
                    drug_name = correct_drug_name(drug, substitutes['Ingredient'])

                #print results of alternatives
                prices = list(substitutes['Price'])
                subs = list(substitutes['Trade_Name'])
                result.append({'name':drug_name.upper(),'num':n,'s':subs,'p':prices})
            else:
                no.append(drug)

        return render_template("automed_success.html", result = result,no=no)

if __name__ == "__main__":
    app.run('0.0.0.0')(debug=False)
