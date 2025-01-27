from flask import Flask, request, render_template, redirect, url_for, jsonify, session
from pymongo import MongoClient
import requests
from functools import wraps
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
import hashlib
import secrets
import os
from os.path import join, dirname

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)
app.secret_key = "BI123"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/sign_in", methods=["POST"])
def sign_in():
    # Sign in
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    result = db.users.find_one(
        {
            "username": username_receive,
            "password": pw_hash,
        }
    )
    if result:
        session["logged_in"] = True
        session["username"] = result["username"]
        return jsonify(
            {
                "result": "success",
            }
        )
    else:
        return jsonify(
            {
                "msg": "salah",
            }
        )

@app.route("/signup")
def signup():
    return render_template('signup.html')

@app.route("/sign_up/check_dup", methods=["POST"])
def check_dup():
    username_receive = request.form["username_give"]
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({"result": "success", "exists": exists})

@app.route("/sign_up/save", methods=["POST"])
def sign_up():
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    password_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    doc = {
        "username": username_receive,
        "password": password_hash,
    }
    db.users.insert_one(doc)
    return jsonify({"result": "success"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def main():
    words_result = db.words.find({'username': session.get("username")}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    return render_template('index.html', words=words)



@app.route("/eror")
@login_required
def eror():
    msg = request.args.get("msg")
    isi = request.args.get("isi")
    saran = request.args.get("saran")
    return render_template('eror.html', msg=msg,isi=isi,saran=saran)

@app.route("/detail/<keyword>")
@login_required
def detail(keyword):
    api_key = "78a7ed44-2013-47ea-8b24-b46e270ccfab"
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()

    if not definitions:
        return redirect(url_for(
            "eror",
            msg = keyword,
            isi = "aneh"
        ))
    
    if type(definitions[0]) is str:
        saran = ", ".join(definitions)
        return redirect(url_for(
            "eror",
            msg = f'Cloud not find the word, "{keyword}", did you mean one of these words: ',
            isi = "gak terlalu aneh",
            saran = saran
        ))

    status = request.args.get("status_give", "new")
    return render_template(
        'detail.html',
        word=keyword,
        definitions=definitions,
        status = status
    )

@app.route("/api/save_word", methods=["POST"])
@login_required
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'username': session.get("username"),
        'word': word,
        'definitions': definitions,
        "date" : datetime.now().strftime("%Y%m%d")
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })

@app.route("/api/delete_word", methods=["POST"])
@login_required
def delete_word():
    word = request.form.get('word_give')
    filter_query = {'word': word, 'username': session.get("username")}
    db.words.delete_one(filter_query)
    db.examples.delete_many({"word": word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was deleted'
    })

@app.route('/api/get_exs', methods=['GET'])
@login_required
def get_exs():
    word = request.args.get("word")
    example_data = db.examples.find({"word": word})
    examples = []
    for example in example_data:
        examples.append({
            "example": example.get("example"), 
            "id": str(example.get("_id"))
        })
    return jsonify({
        "result": "success", 
        "examples": examples
    })

@app.route("/api/save_ex", methods=["POST"])
@login_required
def save_ex():
    word = request.form.get("word")
    example = request.form.get("example")
    doc = {
        "word": word,
        "example": example,
    }
    db.examples.insert_one(doc)
    return jsonify(
        {
            "result": "success",
            "msg": f'Your example, {example}, for {word} was saved!',
        }
    )


@app.route("/api/delete_ex", methods=["POST"])
@login_required
def delete_ex():
    id = request.form.get("id")
    word = request.form.get("word")
    db.examples.delete_one({"_id": ObjectId(id)})
    return jsonify(
        {
            "result": "success", 
            "msg": f'Your example for the word, {word}, was deleted !'
        }
    )

if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)    