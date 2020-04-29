from flask import Flask, render_template, request,jsonify
import pandas as pd
import numpy as np
import requests
import json
from tesserocr import PyTessBaseAPI
import sys
import spacy  #pip install -U spacy
import scispacy  #pip install scispacy
import en_ner_bc5cdr_md  #pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.4/en_ner_bc5cdr_md-0.2.4.tar.gz
import re
import Levenshtein as lev #pip install python-levenshtein
MATCH_RATIO = 0.8
import xmltodict

#levenstiend dist search with match ratio
def search(drug,row):
    try:
        if drug in row:
            return True
        else:
            for word in row:
                #Levenshtein distance ratio
                ratio = lev.ratio(drug, word)
                if ratio > MATCH_RATIO:
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
                if ratio > MATCH_RATIO:
                    return word
            return False

#extract biomedical information from extracted text
nlp = en_ner_bc5cdr_md.load()
def detect_drugs(text):
        #NLP model for drug recognition
        #nlp = en_ner_bc5cdr_md.load()
        #the input text file
        #use NLP model to parse the text

        parsed_text = nlp(text)
        #extract entities/ drug names
        entities = parsed_text.ents
        #print entities
        print("List of entities:", entities)
        return entities

#do OCR on the uploaded image
def getOCR():
    '''
    Function to do OCR on image

    :rtype : List of biomedical entities
    '''
    extract = ''
    with PyTessBaseAPI() as api:
        api.SetImageFile('pres.jpg')
        extract=detect_drugs(api.GetUTF8Text())
        api.AllWordConfidences()
    search =' '.join([token.orth_ for token in extract])
    return re.findall(r'[a-zA-Z]+',search)
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
        file = request.files['imgFile'] ## byte file
        file.save('pres.jpg')
        return handle_data_backend(getOCR())

@app.route('/handle_data', methods=['POST','GET'])
def handle_data():
        if request.method == "POST":            
                new_pres_drug = request.form['drug']
                new_pres_drug = new_pres_drug.lower().split(",")
                result = []
                no = []
                url = "https://rxnav.nlm.nih.gov/REST/rxcui?name="
                ids = []
                #interaction=[]
                for drug in new_pres_drug:  
                        #interaction.append(getRxCui(drug))
                        a = drug_data.apply(lambda row : search(drug,row['Ingredient']), axis = 1)
                        b = drug_data.apply(lambda row : search(drug,row['Name']), axis = 1)
                        substitutes = drug_data[a | b].sort_values('Price').head(5)
                        n = len(substitutes)

                        if n > 0 and drug:
                            drug_name = correct_drug_name(drug, substitutes['Name'])
                            if not drug_name:
                                drug_name = correct_drug_name(drug, substitutes['Ingredient'])
                            prices = list(substitutes['Price'])
                            subs = list(substitutes['Trade_Name'])
                            result.append({'name':drug_name.upper(),'num':n,'s':subs,'p':prices})
                        else:
                            no.append(drug.upper())
                        
                        drug_id = xmltodict.parse(requests.get(url+drug_name).text)
                        response = drug_id['rxnormdata']['idGroup']
                        if 'rxnormId' in response:
                            ids.append(response['rxnormId'])
                warnings=[]

                url = "https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis="
                interactions = requests.get(url+"+".join(ids)).json()
                if 'fullInteractionTypeGroup' in interactions:
                    for j in interactions['fullInteractionTypeGroup'][0]['fullInteractionType']:
                        warnings.append([j['interactionPair'][0]['description'],j['minConcept'][0]['name'],j['minConcept'][1]['name']])
                return render_template("automed_success.html", result = result, no=no, warnings=warnings)
    

def handle_data_backend(new_pres_drug): 
        result = []
        no = []
        url = "https://rxnav.nlm.nih.gov/REST/rxcui?name="
        ids = []
        #interaction=[]         
        for drug in new_pres_drug:  
                #interaction.append(getRxCui(drug))
                a = drug_data.apply(lambda row : search(drug.lower(),row['Ingredient']), axis = 1)
                b = drug_data.apply(lambda row : search(drug.lower(),row['Name']), axis = 1)
                substitutes = drug_data[a | b].sort_values('Price').head(5)
                n = len(substitutes)

                if n > 0 and drug:
                    drug_name = correct_drug_name(drug, substitutes['Name'])
                    if not drug_name:
                        drug_name = correct_drug_name(drug, substitutes['Ingredient'])
                    prices = list(substitutes['Price'])
                    subs = list(substitutes['Trade_Name'])
                    result.append({'name':drug_name.upper(),'num':n,'s':subs,'p':prices})
                else:
                    no.append(drug.upper())
                #find interaction of this drug
                drug_id = xmltodict.parse(requests.get(url+drug_name).text)
                response = drug_id['rxnormdata']['idGroup']
                if 'rxnormId' in response:
                    ids.append(response['rxnormId'])

        new_pres_drug = request.form['drug']
        new_pres_drug = new_pres_drug.lower().split(",")

        warnings = []

        url = "https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis="
        interactions = requests.get(url+"+".join(ids)).json()
        if 'fullInteractionTypeGroup' in interactions:
            for j in interactions['fullInteractionTypeGroup'][0]['fullInteractionType']:
                warnings.append([j['interactionPair'][0]['description'],j['minConcept'][0]['name'],j['minConcept'][1]['name']])
        return render_template("automed_success.html", result = result, no=no, warnings=warnings)



if __name__ == "__main__":
    app.run('0.0.0.0')(debug=False)
    #socketio.run(app, debug=True)
