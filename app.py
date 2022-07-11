from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('mongodb+srv://sonsungwoo:s71006248@cluster0.1kvsuvl.mongodb.net/?retryWrites=true&w=majority')
db = client.dbsparta

@app.route('/')
def home():
    return render_template('index.html');

@app.route("/mars", methods=["POST"])
def web_mars_post():
    name_receive = request.form['name_give']
    address_receive = request.form['address_give']
    size_receive = request.form['size_give']
    doc = {
        'name' : name_receive,
        'address' : address_receive,
        'size' : size_receive,
        'price' : int(size_receive.split('평')[0])*500
    }
    db.mars.insert_one(doc)
    return jsonify({'msg': '주문 완료!'});

@app.route("/mars", methods=["GET"])
def web_mars_get():

    all_list = list(db.mars.find({}, {'_id': False}))
    return jsonify({'all_list': all_list});

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)
