from re import U
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, Response
import json
import uuid
import time
from datetime import date
from collections import ChainMap
import os
from bson.objectid import ObjectId

#Connect to local MongoDB
mongodb_hostname = os.environ.get("MONGO_HOSTNAME","localhost")
client = MongoClient('mongodb://'+mongodb_hostname+':27017/')

# Database
db = client['DigitalNotes']

#Collections
notes = db['Notes']
users = db['Users']

#Flask
app = Flask(__name__)

users_session = {}
admin_session = {}
user_notes = []

def create_session(email , category):
    user_uuid = str(uuid.uuid1())
    if category == "admin":
        admin_session[user_uuid] = (email, time.time())
        return user_uuid 

    else:
        users_session[user_uuid] = (email, time.time())
        return user_uuid 


def is_session_valid(user_uuid):
    return user_uuid in users_session

def is_session_valid_admin(user_uuid):
    return user_uuid in admin_session


#Dimioyrgia
@app.route('/createUser', methods=['POST'])
def create_user():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not "name" in data or not "password" in data or not "username" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
        
  

    result = users.count_documents( {"email" : data['email']})
    result2 = users.count_documents({'username' : data['username']})

    if (result > 0 or result2 > 0) : 
        return Response("A user with the given email or username already exists ", mimetype='application/json' , status=400)
    else: 
        data['category'] = "user"
        users.insert(data)
        return Response(data['name']+" was added to the MongoDB", mimetype='application/json' , status=200) 
     


#Eisodos
@app.route('/login', methods=['POST'])
def login():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not "password" in data or not "username" in data or not "category" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")

    
    resultInfo = users.find_one( {"email" : data['email'] ,"username" : data['username'] , "password" : data['password']})

    if resultInfo : 
        email = data['email']
        username = data['username']
        password = resultInfo['password']
        category = resultInfo['category']
        user_uuid = create_session(email ,username, password,category)
        res = {"uuid": user_uuid, "email": data['email'], "username": data['username']}
        return Response(json.dumps(res), mimetype='application/json' , status=200)   
    else:  
       return Response("Wrong username/email or password.",mimetype='application/json', status=400)
    
#Prosthiki
@app.route('/addToNotes', methods=['POST'])
def addto_notes():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "title" in data or not "date" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
  


    uuid = request.headers.get('authorization')

    if (is_session_valid(uuid)) :

        note = {}
        result = note.find_one({"_title" : ObjectId(data['title'])})
        if result:
            result['_title'] = str(result['_title'])
            note['title'] = str(result['_title'])
            note['text'] = result['text']
            note['key_word'] = result['key-word']
            note['date']= result['date']
            user_notes.append(note)
            return Response(json.dumps(result), mimetype='application/json' , status=200)

        else:
            return Response("No notes found!", mimetype='application/json' , status=400)
    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)


#Anazitisi
@app.route('/searchNotes', methods=['GET'])
def search_notes():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "title" in data  or not "key_word" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
  

    found_notes = []
    uuid = request.headers.get('authorization')

    if "title" in data :
         res = found_notes.find_one( {"_title" : ObjectId(data["title"])})
         if res:
            res['notes'] = str(res['_title'])          
            return Response(json.dumps(res), mimetype='application/json' , status=200)
         else:
                return Response("No notes found with this given title!", mimetype='application/json' , status=400)

    if "key_word" in data :
         res = found_notes.find_one( {"_key_word" : ObjectId(data["title"])})
         if res:
              res['notes'] = str(res['_title'])
              return Response(json.dumps(res), mimetype='application/json' , status=200)
         else:
               return Response("No notes found with this given key word!", mimetype='application/json' , status=400)


#Diorthosi/Allagi
@app.route('/updateNote', methods=['PATCH'])
def update_note():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "title" in data and not "text" in data and not "key_word" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
  

    uuid = request.headers.get('authorization')

    result = user_notes.find_one( {"_title" : ObjectId(data["title"])})

    if result: 

        if "title" in data:
            user_notes.update_one({"_title": ObjectId(data["title"])} , { '$set':{'title' : data['title']}})

        if "text" in data:
            user_notes.update_one({"_title": ObjectId(data["title"])} , { '$set':{'text' : data['text']}})

        if "key_word" in data:
            user_notes.update_one({"_title": ObjectId(data["title"])} , { '$set':{'key_word' : data['key_word']}})

        if "category" in data:
            notes.update_one({"_title": ObjectId(data["title"])} , { '$set':{'category' : data['category']}})
              
        res= notes.find_one( {"_title" : ObjectId(data["title"])})
        res['_title'] = str(res['_title'])
        return Response(json.dumps(res), mimetype='application/json' , status=200)
    else: 
        return Response("There is no notes with that given title! ", mimetype='application/json' , status=400)
    

#Diagrafi
@app.route('/deleteUserNotes', methods=['DELETE'])
def deleteUser_notes():

    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "title" in data :
        return Response("Information incomplete",status=500,mimetype="application/json")
    
    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)) :
        for i in range(len(user_notes)):
            if user_notes[i]['title'] == data['title']:
                del user_notes[i]
                res = {"Notes": user_notes}

                return Response(json.dumps(res), mimetype='application/json' , status=200)
            
        else:
                return Response("This title is not in your notes!" , mimetype='application/json' , status=400)


    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)


#Emfanish
@app.route('/showNotes', methods=['GET'])
def show_notes():
    
    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)):
        
        res = {"Notes": user_notes }
        return Response(json.dumps(res), mimetype='application/json' , status=200)
        user  = users_session[uuid]
        result = users.find_one({'email' : user[0]})
        testResult = users.count({"email":user[0] , "OrderNotes": {"$exists":True}})
        if testResult>0:
            allNotes = result['OrderNotes']
            return Response(json.dumps(allNotes) ,mimetype='application/json' , status=200)
        else:
            return Response ("Your notes are empty!" , status = 400)
    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)




#Diagrafi Logariasmoy
@app.route('/deleteUser', methods=['DELETE'])
def delete_user():
    
    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)) :

        user  = users_session[uuid]
        users.delete_one({"email" : user[0]})
        users_session.clear()
    
        return Response("User deleted!" , mimetype='application/json' , status=200)
    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)





#Eisagwgi Admin
@app.route('/addAdmin', methods=['PATCH'])
def add_admin():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not "name" in data or not "password" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
  

    uuid = request.headers.get('authorization')

    if (is_session_valid_admin(uuid)) :
        result = users.count_documents( {"email" : data["email"]})

        if (result > 0): 
            return Response("A user with that given email already exists ", mimetype='application/json' , status=400) 
        else:  
            users_session.insert(data)
            return Response(data['email']+" was added to the MongoDB", mimetype='application/json' , status=200) 
    else:
        return Response ("You need to be logged in as an admin , in order to perfmorm this action!" , status = 401)


#Diagrafi User
@app.route('/deleteUser', methods=['DELETE'])
def delete_user():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "title" in data :
        return Response("Information incomplete",status=500,mimetype="application/json")
  


    uuid = request.headers.get('authorization')

    if (is_session_valid_admin(uuid)) :
        result = users_session.find_one( {"username" : ObjectId(data["username"])})

        if result: 
            users_session.delete_one( {"_username" : ObjectId(data["username"])})
            msg = "{} was deleted.".format(result['title'])
            return Response(msg, mimetype='application/json' , status=200) 
        else:  
            return Response("No users found with this given username!", mimetype='application/json' , status=400) 
    else:
        return Response ("You need to be logged in as an admin , in order to perfmorm this action!" , status = 401)


# Εκτέλεση flask service σε debug mode, στην port 5000. 
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
