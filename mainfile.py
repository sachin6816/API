

#Importing important Libraries
import sqlite3
import time
import pandas as pd
from transformers.pipelines import pipeline
from flask import Flask
from flask import request
from flask import jsonify
import os

#Create Flask App
app = Flask(__name__)

#Connecting to Database
connection = sqlite3.connect('database.db')
cur = connection.cursor()
connection.execute('DROP TABLE IF EXISTS models')
#Creating Table models
connection.execute("CREATE TABLE models(name TEXT, tokenizer TEXT, model TEXT)")

#Inserting details of models 
cur.execute("INSERT INTO models VALUES ('distilled-bert','distilbert-base-uncased-distilled-squad','distilbert-base-uncased-distilled-squad')")
cur.execute("INSERT INTO models VALUES ('deepset-roberta','deepset/roberta-base-squad2','deepset/roberta-base-squad2')")
connection.commit()

#Create Table to store 
cur.execute("CREATE TABLE IF NOT EXISTS qa_log(question TEXT, context TEXT, answer TEXT, model TEXT,timestamp REAL)")

#-----------------------------------------Models ----------------------

@app.route('/models', methods=['GET','PUT','DELETE'])
def methods_for_models():
   
    if  request.method =='GET':
        connection  =  sqlite3.connect('database.db')
        cursor  =  connection.cursor()
        cursor.execute('''SELECT name,tokenizer,model  FROM models''')
        result = cursor.fetchall()
        model=[]
        for i in range(0,len(result)):
            record = {"name": result[i][0] ,"tokenizer":result[i][1]  ,"model": result[i][2] }
            model.append(record)
        return jsonify(model)

    elif request.method == 'PUT':
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()
       
        #Getting details of the new model 
        data = request.json
        name = data['name']
        tokenizer = data['tokenizer']
        model = data['model']
       
        #Inserting new mnodel
        connection.execute("INSERT INTO models (name, tokenizer, model) VALUES (?, ?, ?)", (name, tokenizer, model))
        connection.commit()
        #Query to retrieve models from database
        cur.execute("SELECT name,tokenizer,model FROM models")
        #Storing Results of the query
        result = cur.fetchall()
        model = []
        #Storing the Results in JSON format
        for i in range(0,len(result)):
            record = {"name": result[i][0] ,"tokenizer":result[i][1]  ,"model": result[i][2]}
            model.append(record)
        return jsonify(model)
   
    elif request.method == 'DELETE':
        connection = sqlite3.connect("database.db")
        cur = connection.cursor()
        #Getting details of the model to be deleted in the Table
        modelname = request.args.get('model',None)
        #Deleting the entire row
        cur.execute("DELETE FROM models WHERE name = ?", (modelname,))
        connection.commit()
        #Query to retrieve models from database
        cur.execute("SELECT name,tokenizer,model FROM models")
        result = cur.fetchall()
        #Storing the Result in JSON format
        model = []
        for i in range(0,len(result)):
            record = {"name": result[i][0] ,"tokenizer":result[i][1]  ,"model": result[i][2]}
            model.append(record)
        return jsonify(model)

#-----------------------------------------Answers ----------------------

@app.route("/answer", methods = ['GET','POST'])
def methods_for_answers():
   
    if  request.method =='POST':
        name = request.args.get('model', None)
        data = request.json
        #Default model when no model is specified
        if not name:
            name='distilled-bert'    
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()
        #Query to retireve information of that particular model
        cur.execute("SELECT DISTINCT name,tokenizer,model FROM models WHERE name=?",(name,))
        result = cur.fetchall()
       
        row= result[0]
        name = row[0]
        tokenizer = row[1]
        model = row[2]
   
        #Implementing the  Models
        hg_comp = pipeline('question-answering', model=model, tokenizer=tokenizer)

        # Answering the Question
        answer = hg_comp({'question': data['question'], 'context': data['context']})['answer']

        #Generating Timestamp
        ts = time.time()

        #Inserting entry into qa_log table
        cur.execute("CREATE TABLE IF NOT EXISTS qa_log(question TEXT, context TEXT, answer TEXT, model TEXT,timestamp REAL)")
        cur.execute("INSERT INTO qa_log VALUES(?,?,?,?,?)", (data['question'], data['context'],answer, name,ts))
        connection.commit()


        cur.close()
        connection.close()

        #JSON to return Output
        output = {
        "timestamp": ts,
        "model": name,
        "answer": answer,
        "question": data['question'],
        "context": data['context']}  
        return jsonify(output)


    elif  request.method =='GET':
        name= request.args.get('model')
        start= request.args.get('start')
        end= request.args.get('end')
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()
        if name:
            cur.execute('SELECT * FROM qa_log WHERE model=? AND timestamp >=? AND timestamp <=?',(name,start,end))
            model = cur.fetchall()
            output=[]
            for row in model:
              record = {"timestamp": row[4],
                        "model":row[3],
                        "answer": row[2],
                        "question": row[0],
                        "context": row[1]}
              output.append(record)
            return jsonify(output)
        else:
            cur.execute('SELECT * FROM qa_log WHERE timestamp >=? AND timestamp <=?',(start,end))
            model = cur.fetchall()
            output=[]
            for row in model:
              record = {"timestamp": row[4],
                        "model":row[3],
                        "answer": row[2],
                        "question": row[0],
                        "context": row[1]}
              output.append(record)
            return jsonify(output)


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), threaded=True)
   app.debug=True
