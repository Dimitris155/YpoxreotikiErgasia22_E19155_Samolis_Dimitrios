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

# Connect to our local MongoDB
mongodb_hostname = os.environ.get("MONGO_HOSTNAME","localhost")
client = MongoClient('mongodb://'+mongodb_hostname+':27017/')

# Choose database
db = client['DigitalNotes']

# Choose collections
notes = db['Notes']
users = db['Users']

# Initiate Flask App
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


#CreateUser
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
     


#LoginUser
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
    if not "email" in data or not "password" in data or not "category" in data:
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
    


#Note Searching
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
    if not "title" in data  or not "key_word" in data and not "category" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
  

    found_notes = []
    uuid = request.headers.get('authorization')

    if (is_session_valid(uuid)) :

        if "title" in data :
            res = found_notes.find_one( {"_title" : ObjectId(data["title"])})
            if res:
                res['notes'] = str(res['_title'])
                return Response(json.dumps(res), mimetype='application/json' , status=200)
            else:
                return Response("No notes found with this given title!", mimetype='application/json' , status=400)

    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)
    
    if (is_session_valid(uuid)) :

        if "key_word" in data :
            res = found_notes.find_one( {"_key_word" : ObjectId(data["title"])})
            if res:
                res['notes'] = str(res['_title'])
                return Response(json.dumps(res), mimetype='application/json' , status=200)
            else:
                return Response("No notes found with this given key word!", mimetype='application/json' , status=400)

        if "category" in data:
            res = notes.find( {"category" : data['category']})
        else:
            return Response("No product found with this gived category!", mimetype='application/json' , status=400)
    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)


#Add To Notes
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
    if not "title" in data or not "date" in data and not "category" in data:
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




#Show my Notes
@app.route('/showNotes', methods=['GET'])
def show_notes():
    
    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)) :
        res = {"Notes": user_notes }
        return Response(json.dumps(res), mimetype='application/json' , status=200)

    else:
        return Response ("You need to be logged in, in order to perfmorm this action!" , status = 401)




#DElete from my notes
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


#Delete my account
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


#My Notes ordered chronologically
@app.route('/showAllNotes', methods=['GET'])
def show_allNotes():

    
    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)) :

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



#Add a new Note
@app.route('/addNote', methods=['PATCH'])
def add_note():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "title" in data or not "text" in data or not "key_word" in data and not "category" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
  

    uuid = request.headers.get('authorization')

    if (is_session_valid_admin(uuid)) :
        result = notes.count_documents( {"title" : data["title"]})

        if (result > 0): 
            return Response("A note with that given title already exists ", mimetype='application/json' , status=400) 
        else:  
            user_notes.insert(data)
            return Response(data['title']+" was added to the MongoDB", mimetype='application/json' , status=200) 
    else:
        return Response ("You need to be logged in as an admin , in order to perfmorm this action!" , status = 401)


#Detele a note
@app.route('/deleteNote', methods=['DELETE'])
def delete_note():
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
        result = user_notes.find_one( {"_title" : ObjectId(data["title"])})

        if result: 
            user_notes.delete_one( {"_title" : ObjectId(data["title"])})
            msg = "{} was deleted.".format(result['title'])
            return Response(msg, mimetype='application/json' , status=200) 
        else:  
            return Response("No notes found with this given title!", mimetype='application/json' , status=400) 
    else:
        return Response ("You need to be logged in as an admin , in order to perfmorm this action!" , status = 401)


#Update a Note
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

    if (is_session_valid_admin(uuid)) :
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
    
    else:
        return Response ("You need to be logged in as an admin , in order to perfmorm this action!" , status = 401)



# Εκτέλεση flask service σε debug mode, στην port 5000. 
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
