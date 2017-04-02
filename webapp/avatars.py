from flask_oauthlib.client import OAuth
from webapp import app
from flask import session, redirect, request, render_template
import json, os, urllib, random
from functools import wraps
site = os.environ['SITE']
api = os.environ['API']

oauth = OAuth(app)

faforever = oauth.remote_app('faforever',
    consumer_key=os.environ['CONSUMER_KEY'],
    consumer_secret=os.environ['CONSUMER_SECRET'],
    base_url=api+"/oauth/authorize",
    access_token_url=api+"/oauth/token",
    request_token_params={"scope":"public_profile"}
)

@app.route("/")
def root():
    return render_template("home.html")

@app.route("/login")
def login():
    return faforever.authorize(callback=site+"/oauth")


@app.route('/oauth',methods=["GET","POST"])
def oauth_return():
    resp = faforever.authorized_response()
    if resp is None:
        return redirect("/fail")
    token = resp["access_token"]
    session['token'] = token

    return redirect("/avatars")

def get_token(f):
    @wraps(f)
    def df(*args, **kwargs):
        # See if there is an OAuth token for this user
        token = session.get("token")
        if not token:
            # Return to home page, user can login from there
            return redirect("/")
        return f(token, *args, **kwargs)
    return df
    
@app.route('/avatars',methods=["GET"])
@get_token
def avatars(token):
    avatar_list = []
    req = urllib.request.Request(url=api+"/avatar")
    resp = urllib.request.urlopen(req)
    all_avas = json.loads(resp.read().decode("utf8"))

    for r in all_avas:
        avatar_list.append((r["url"],r["id"],r["tooltip"],"?"))

    avatar_list = sorted(avatar_list,key=lambda x: x[1])
    return render_template("avatar_list.html",avatar_list=avatar_list)
    

@app.route('/users',methods=["GET"])
@get_token
def users(token):
    return render_template("find_user.html")

@app.route('/users',methods=["POST"])
@get_token
def users_post(token):
    user = request.form.get("user").strip()
    method = request.form.get("submit")
    if len(user) == 0:
        return redirect("/users")
    req = urllib.request.Request(url=api+"/players/prefix/"+user,method="GET")
    resp = urllib.request.urlopen(req)
    datas = json.loads(resp.read().decode("utf8"))["data"]
    if method == 'go':
        for d in datas:
            if d["attributes"]["login"].lower() == user.lower():
                return redirect("/user_details?id="+d["attributes"]["id"])
        if len(datas) > 0:
            return redirect("/user_details?id="+datas[0]["attributes"]["id"])
    elif method == 'search':
        return render_template("user_list.html", users=[data["attributes"] for data in datas])
    return redirect("/users")

@app.route('/avatar_details',methods=["GET"])
@get_token
def avatardetails(token):
    user_list = []
    aid = request.args.get("id")
    try:
        int(aid)
    except:
        return redirect("fail")

    req = urllib.request.Request(url=api+"/avatar/"+str(aid)+"/users")
    resp = urllib.request.urlopen(req)
    ava_users = json.loads(resp.read().decode("utf8"))

    req = urllib.request.Request(url=api+"/avatar/"+str(aid))
    resp = urllib.request.urlopen(req)
    avatar = json.loads(resp.read().decode("utf8"))

    creation_times = ["30/07/1966"]
    expiry_times = ["32/13/2666"]
    # The requirements explicitly state that expiry times should be included.
    for i in range(0,100):
        expiry_times.append("{}/{}/{}".format(random.randint(1,28),random.randint(1,12),random.randint(2017,2020)))
        creation_times.append("{}/{}/{}".format(random.randint(1,28),random.randint(1,12),random.randint(2012,2017)))


    for u in ava_users:
        creation = creation_times[random.randint(0,len(creation_times)-1)]
        expiry = expiry_times[random.randint(0,len(expiry_times)-1)]

        user_list.append((u["login"],u["id"],creation,expiry))

    return render_template("avatar_details.html",user_list=user_list,avatar=(avatar["url"],avatar["id"],avatar["tooltip"]))

@app.route('/user_details',methods=["GET"])
@get_token
def userdetails(token):
    avatar_list = []
    uid = request.args.get("id")
    try:
        int(uid)
    except:
        return redirect("fail")
    req = urllib.request.Request(url=api+"/user_avatars?id="+str(uid))
    resp = urllib.request.urlopen(req)
    all_avas = json.loads(resp.read().decode("utf8"))

    for r in all_avas:
        avatar_list.append((r["url"],r["id"],r["tooltip"]))

    req = urllib.request.Request(url=api+"/players/"+str(uid))
    resp = urllib.request.urlopen(req)
    login = json.loads(resp.read().decode("utf8"))["data"]["attributes"]["login"]

    avatar_list = sorted(avatar_list,key=lambda x: x[1])
    return render_template("user_details.html",avatar_list=avatar_list,uid=uid,login=login)

@app.route('/remove_avatar',methods=["GET"])
@get_token
def removeavatar(token):
    callback = request.args.get("callback")
    aid = request.args.get("aid")
    uid = request.args.get("uid")
    if not uid or not aid:
        return redirect("/fail")

    req = urllib.request.Request(url=api+"/user_avatars",method="DELETE",headers={"Authorization":"Bearer " + token})
    resp = urllib.request.urlopen(req,data=urllib.parse.urlencode({"avatar_id":int(aid),"user_id":int(uid)}).encode("utf8"))
    if callback == "u":
        return redirect("/user_details?id="+str(uid))
    if callback == "a":
        return redirect("/avatar_details?id="+str(aid))
    return redirect("/fail")

@app.route('/add_avatar',methods=["POST"])
@get_token
def addavatar(token):
    aid = request.args.get("id")
    users = request.form.get("users").split(" ")
    for user in users:
        req = urllib.request.Request(url=api+"/players/prefix/"+user,method="GET")
        resp = urllib.request.urlopen(req)
        datas = json.loads(resp.read().decode("utf8"))["data"]
        for d in datas:
            if d["attributes"]["login"].lower() == user.lower():
                req = urllib.request.Request(url=api+"/user_avatars",method="POST",headers={"Authorization":"Bearer " + token})
                resp = urllib.request.urlopen(req,data=urllib.parse.urlencode({"avatar_id":int(aid),"user_id":d["attributes"]["id"]}).encode("utf8"))
                break
    return redirect("/avatar_details?id="+str(aid))

@app.route('/delete_avatar',methods=["GET"])
@get_token
def deleteavatar(token):
    aid = request.args.get("id")
    req = urllib.request.Request(url=api+"/avatar",method="DELETE",headers={"Authorization":"Bearer " + token})
    resp = urllib.request.urlopen(req,data=urllib.parse.urlencode({"id":aid}).encode("utf8"))
    return redirect("/avatars")

@app.route('/delete_user',methods=["GET"])
@get_token
def deleteuser(token):
    return render_template("delete_user.html")

@app.route('/fail')
def fail():
    return render_template("fail.html",site=site)
