from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from pyaspeller import YandexSpeller
from deepmultilingualpunctuation import PunctuationModel
from gramformer import Gramformer
import language_tool_python
import re
import json 

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///corrections.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class Correction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_input = db.Column(db.Text, nullable=False)
    corrected_output = db.Column(db.Text, nullable=False)
    all_errors = db.Column(db.Integer, nullable=False)
    capitalization_errors = db.Column(db.Integer, nullable=False)
    spelling_errors = db.Column(db.Integer, nullable=False)
    grammar_errors = db.Column(db.Integer, nullable=False)
    punctuation_errors = db.Column(db.Integer, nullable=False)
    error_details = db.Column(db.Text, nullable=False)  # Store all error details as JSON

# Initialize modules
speller = YandexSpeller()
punctuation_model = PunctuationModel()
gf = Gramformer(models=1)
tool = language_tool_python.LanguageTool('en-US')

# Correction functions
def correct_spelling(text):
    corrected_text = speller.spelled(text)
    corrections = []

    original_words = text.split()
    corrected_words = corrected_text.split()

    for original, corrected in zip(original_words, corrected_words):
        if original != corrected:
            corrections.append((original, corrected))

    return corrections, corrected_text

def correct_punctuation(text):
    corrected_text = punctuation_model.restore_punctuation(text)
    corrections = []

    original_words = text.split()
    corrected_words = corrected_text.split()

    for original, corrected in zip(original_words, corrected_words):
        if original != corrected:
            corrections.append((original, corrected))

    return corrections, corrected_text

def correct_grammar(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    corrections = []
    corrected_text_list = []

    for sentence in sentences:
        corrected_sentence = gf.correct(sentence)
        if isinstance(corrected_sentence, set):
            corrected_sentence = next(iter(corrected_sentence))

        corrected_text_list.append(corrected_sentence)
        original_words = sentence.split()
        corrected_words = corrected_sentence.split()

        i, j = 0, 0
        while i < len(original_words) or j < len(corrected_words):
            if i < len(original_words) and j < len(corrected_words):
                if original_words[i] != corrected_words[j]:
                    if original_words[i] not in corrected_words[j:]:
                        corrections.append((original_words[i], corrected_words[j]))
                        i += 1
                        j += 1
                    else:
                        corrections.append((" ", corrected_words[j]))
                        j += 1
                else:
                    i += 1
                    j += 1
            elif j < len(corrected_words):
                corrections.append((" ", corrected_words[j]))
                j += 1
            else:
                i += 1

    corrected_text = " ".join(corrected_text_list)
    return corrections, corrected_text

def correct_capitalization(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    corrections = []  
    corrected_sentences = []

    for sentence in sentences:
        if not sentence:
            continue

        words = sentence.split()
        first_word = words[0]
        if first_word[0].islower():
            corrected_word = first_word.capitalize()
            corrections.append((first_word, corrected_word))
            words[0] = corrected_word

        sentence = " ".join(words)
        matches = tool.check(sentence)
        for match in matches:
            if match.replacements:
                start, end = match.offset, match.offset + match.errorLength
                incorrect_text = sentence[start:end]
                suggested_replacement = match.replacements[0]
                corrections.append((incorrect_text, suggested_replacement))
                sentence = sentence[:start] + suggested_replacement + sentence[end:]

        corrected_sentences.append(sentence)

    corrected_text = " ".join(corrected_sentences)
    return corrections, corrected_text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/correct', methods=['POST'])
def correct_text():
    text = request.form['text']
    corrections = {
        "all": [],
        "capitalization": [],
        "spelling": [],
        "grammar": [],
        "punctuation": []
    }
    counts = {
        "capitalization": 0,
        "spelling": 0,
        "grammar": 0,
        "punctuation": 0,
        "all": 0  # Add this to track total errors
    }

    # Apply corrections in order
    spell_corrections, text = correct_spelling(text)
    corrections["spelling"].extend(spell_corrections)
    counts["spelling"] = len(spell_corrections)

    punct_corrections, text = correct_punctuation(text)
    corrections["punctuation"].extend(punct_corrections)
    counts["punctuation"] = len(punct_corrections)

    grammar_corrections, text = correct_grammar(text)
    corrections["grammar"].extend(grammar_corrections)
    counts["grammar"] = len(grammar_corrections)

    capital_corrections, text = correct_capitalization(text)
    corrections["capitalization"].extend(capital_corrections)
    counts["capitalization"] = len(capital_corrections)

    # Combine all corrections and calculate total errors
    for key in corrections:
        if key != "all":
            corrections["all"].extend(corrections[key])
    
    # Update the total error count
    counts["all"] = counts["capitalization"] + counts["spelling"] + counts["grammar"] + counts["punctuation"]

    # Save to database
    new_correction = Correction(
        user_input=request.form['text'],
        corrected_output=text,
        all_errors=counts["all"],
        capitalization_errors=counts["capitalization"],
        spelling_errors=counts["spelling"],
        grammar_errors=counts["grammar"],
        punctuation_errors=counts["punctuation"],
        error_details=json.dumps(corrections)  # Save all details as JSON
    )
    db.session.add(new_correction)
    db.session.commit()

    return jsonify({
        'corrections': corrections,
        'counts': counts,
        'corrected_text': text
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensures the tables are created
    app.run(debug=True) 