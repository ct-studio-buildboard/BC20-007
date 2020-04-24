#### README #####
# Step 1: Installation
# 	In your Terminal, run these commands to install the required packages:
#
# 		pip install -U spacy
# 		pip install scispacy
# 		pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.4/en_ner_bc5cdr_md-0.2.4.tar.gz

# Step 2: to run from command line
# 	In your Terminal, run this script. <file_name> is the text file to detect drugs from:
# 		python drug_recognition.py <file_name>

# 	Example:
# 		python drug_recognition.py out.txt

# Step 3: To run from code
#	Pass 'text_file' into function 'detect_drugs'


#### Drug Recognition model
import sys
import spacy  #pip install -U spacy
import scispacy  #pip install scispacy
import en_ner_bc5cdr_md  #pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.4/en_ner_bc5cdr_md-0.2.4.tar.gz


def detect_drugs(text_file):
	#NLP model for drug recognition
	nlp = en_ner_bc5cdr_md.load()

	#the input text file
	text = open(text_file, "r").read()

	#use NLP model to parse the text
	parsed_text = nlp(text)

	#extract entities/ drug names
	entities = parsed_text.ents

	#print entities
	print("List of entities:", entities)

	return entities


if __name__ == "__main__":
	#pass file name in command line
	detect_drugs(sys.argv[1])