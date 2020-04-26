from flask import Flask, render_template, request,jsonify
import pandas as pd
import numpy as np
import requests
import json
from tesserocr import PyTessBaseAPI



def getOCR():
    with PyTessBaseAPI() as api:
        api.SetImageFile('pres.jpg')
        print(api.GetUTF8Text())
        api.AllWordConfidences()
#from flask_socketio import SocketIO, emit, join_room, leave_room

# app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
# socketio = SocketIO(app, always_connect=True, engineio_logger=True)

# @socketio.on('connect')
# def connected():
#     print('connect')
    
# @socketio.on('disconnect')
# def disconnect():
#     print('disconnect')


def getRxCui (drugName):
    try:
        response = requests.get('https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term='+drugName)
        string = response.content.decode('utf-8')
        json_obj = json.loads(string)
        return json_obj['approximateGroup']['candidate'][0]['rxcui']
    except Exception:
        return None

def getInteractions (interactionQuery):
    try:
        print('checking Interactions',interactionQuery)
        response = requests.get('https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis='+interactionQuery)
        string = response.content.decode('utf-8')
        json_obj = json.loads(string)
        return json_obj['fullInteractionTypeGroup'][0]['fullInteractionType'][0]['interactionPair'][0]['description']
    except Exception:
        return None


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

# @socketio.on('image-upload')
# def imageUpload(image):
#     emit('send-image', image, broadcast = True)


@app.route("/")
def home():
    return render_template("automed_test.html")
    # return render_template("automed_main.html")


@app.route('/uploadPres' , methods=['POST'])
def get_image():
	file = request.files['imgFile'].read() ## byte file
	file.save('pres.jpg')
	getOCR()
	return jsonify({'status':"SUCCESS"})

@app.route('/handle_data', methods=['POST','GET'])
def handle_data():
	if request.method == "POST":		
		new_pres_drug = request.form['drug']
		new_pres_drug = new_pres_drug.lower().split(",")
		result = []
		no = []
		interaction=[]
		for drug in new_pres_drug:  
			interaction.append(getRxCui(drug))
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
		print(getInteractions("+".join(interaction)))
		return render_template("automed_success.html", result = result,no=no)



if __name__ == "__main__":
    app.run()(debug=True)
    #socketio.run(app, debug=True)