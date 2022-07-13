from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
from bs4 import BeautifulSoup
from pymongo import MongoClient
client = MongoClient('mongodb+srv://sonsungwoo:s71006248@cluster0.1kvsuvl.mongodb.net/?retryWrites=true&w=majority')
db = client.MovieAttae

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'SPARTA'

# JWT 패키지를 사용합니다. (설치해야할 패키지 이름: PyJWT)
import jwt

# 토큰에 만료시간을 줘야하기 때문에, datetime 모듈도 사용합니다.
import datetime

# 회원가입 시엔, 비밀번호를 암호화하여 DB에 저장해두는 게 좋습니다.
# 그렇지 않으면, 개발자(=나)가 회원들의 비밀번호를 볼 수 있으니까요.^^;
import hashlib
import random
import string
import certifi
import requests

#손성우
@app.route('/')
def home():
    print(db.member.find({}));
    token_receive = request.cookies.get('mytoken');
    print('메인페이지 ', token_receive);

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        member_info = db.member.find_one({"memberId": payload['id']})
        return render_template('index.html', memberNick=member_info["memberNick"]);
    except jwt.ExpiredSignatureError:
        return redirect(url_for('loginPage', msg="로그인 시간이 만료되었습니다."));
    except jwt.exceptions.DecodeError:
        return redirect(url_for('loginPage', msg="로그인 정보가 존재하지 않습니다."));

@app.route("/loginPage", methods=["GET"])
def loginPage():
    return render_template('/member/login.html');

@app.route("/member/login", methods=["POST"])
def login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.member.find_one({'memberId': id_receive, 'memberPw': pw_hash})

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=3600)    #언제까지 유효한지
        }
        #jwt를 암호화
        # token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        # token을 줍니다.
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'});

@app.route("/member/kakaologin", methods=["POST"])
def kakaologin():

    id_receive = request.form['id_give']

    result = db.member.find_one({'memberId': id_receive})

    if result is not None:
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=3600)
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '로그인 에러'});

@app.route("/member/joinPage", methods=["GET"])
def joinPage():
    return render_template('/member/join.html');

@app.route("/member/join", methods=["POST"])
def join():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.member.insert_one({'memberId': id_receive, 'memberPw': pw_hash, 'memberNick': nickname_receive})

    return jsonify({'result': 'success'})

@app.route("/member/kakaoJoin", methods=["POST"])
def kakaojoin():
    id_receive = request.form['id_give']

    n = 10
    rand_str = ""
    for i in range(n):
        rand_str += str(random.choice(string.ascii_letters));

    pw_hash = hashlib.sha256(rand_str.encode('utf-8')).hexdigest()
    nickname_receive = request.form['nickname_give']

    db.member.insert_one({'memberId': id_receive, 'memberPw': pw_hash, 'memberNick': nickname_receive})

    return jsonify({'result': 'success'})

@app.route("/member/changePwPage", methods=["GET"])
def changePwPage():
    return render_template('/member/changePw.html');

@app.route("/member/changePw", methods=["POST"])
def changePw():
        id_receive = request.form['id_give']

        idExists = db.member.find_one({'memberId': id_receive});
        if idExists is not None:
            pw_receive = request.form['pw_give']
            pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
            res = db.member.update_one({'memberId': id_receive}, {"$set": {"memberPw": pw_hash}})
            return jsonify({'result': 'success'});
        else:
            return jsonify({'msg': '존재하지 않는 아이디입니다.'});

@app.route("/member/idDuplicateCheck", methods=["POST"])
def idDuplicateCheck():
    id_receive = request.form['id_give']
    idExists = bool
    idExists_temp = db.member.find_one({'memberId': id_receive})
    if idExists_temp is not None:
        idExists = True
    else:
        idExists = False;

    return jsonify({'idExists': idExists});

# 서현웅
# 보낸다
@app.route("/movie", methods=["POST"])
def movie_post():
    url_receive = request.form['url_give']
    star_receive = request.form['star_give']
    comment_receive = request.form['comment_give']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url_receive, headers=headers)
    print(data)

    soup = BeautifulSoup(data.text, 'html.parser')

    title = soup.select_one('meta[property="og:title"]')['content']
    image = soup.select_one('meta[property="og:image"]')['content']
    desc = soup.select_one('meta[property="og:description"]')['content']

    if db.movies.find_one({'title': title}):
        print("중복")
        return jsonify({'msg': '이미 같은 영화 리뷰가 있습니다 !'})
    else:
        print("No 중복")

    id_len = 20
    id_candidate = string.ascii_lowercase + string.digits
    id = ""
    for i in range(id_len):
        id += random.choice(id_candidate)
    doc = {
        'id': id,
        'title': title,
        'image': image,
        'desc': desc,
        'star': star_receive,
        'comment': comment_receive
    }

    db.movies.insert_one(doc)

    return jsonify({'msg': 'Upload complete !'})


@app.route("/movie/update", methods=["POST"])
def movie_update():
    comment_receive = request.form['comment_give']
    print(comment_receive)

    star_receive = request.form['star_give']
    print(star_receive)
    id_receive = request.form['id_give']
    # doc = {
    #     'star': star_receive,
    #     'comment': comment_receive,
    #     'id': id_receive,
    # }

    db.movies.update_one({'id': id_receive}, {'$set': {'star': star_receive}})
    db.movies.update_one({'id': id_receive}, {'$set': {'comment': comment_receive}})
    return jsonify({'msg': '수정 ㅎ Update complete !'})


# 받겠다 (db에서)
@app.route("/movie", methods=["GET"])
def movie_get():
    movie_list = list(db.movies.find({}, {'_id': False}))
    return jsonify({'movies': movie_list})
if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)
