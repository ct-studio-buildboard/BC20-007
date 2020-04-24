from flask import Flask, render_template, request
import pandas as pd
import numpy as np

def search(drug,row):
    try:
        if drug in row:
            return True
        else:
            return False
    except:
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
				prices = list(substitutes['Price'])
				subs = list(substitutes['Trade_Name'])
				result.append({'name':drug.upper(),'num':n,'s':subs,'p':prices})
			else:
				no.append(drug)

		return render_template("automed_success.html", result = result,no=no)

if __name__ == "__main__":
	app.run()(debug=True)