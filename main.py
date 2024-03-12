import asyncio
import re
import threading
import time
from openai import OpenAI
from flask import Flask, request, jsonify
from threading import Thread
import os
import json


app = Flask(__name__)
ASSISTANT_ID = 'asst_0mDLQxnCxppDX7KIGLVdAp4y'
client = OpenAI(api_key='SECRET_API_KEY_HERE')
assistant = client.beta.assistants.retrieve(ASSISTANT_ID)


def show_json(obj):
    print(json.loads(obj.model_dump_json()))


def retrieve_thread():
    if os.path.exists('thread.txt'):
        with open('thread.txt', 'r') as file:
            thread_id = file.read()
            return client.beta.threads.retrieve(thread_id)
    else:
        thread = client.beta.threads.create()
        
        with open('thread.txt', 'w') as file:
            file.write(thread.id)
            
        return thread


def send_message(prompt, thread):
    message = client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=prompt
    )
    
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
    )
    
    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        
        if run.completed_at:
            break
        
        time.sleep(0.5)

    response = client.beta.threads.messages.list(
        thread_id=thread.id, order="asc", after=message.id
    )
    
    print({
        'prompt': prompt,
        'response': json.loads(response.model_dump_json())
    })
    
    try:
        content = response.data[0].content[0]
        result = content.text.value
        result = re.sub('【.*?†source】', '', result)
    except:
        result = 'Lo siento, no tengo información aun sobre eso.'

    return result


@app.route('/message2', methods=['POST'])
def openai():
    data = request.get_json()
    prompt = data['prompt']
    thread_id = data['thread_id']
    #thread = await client.beta.threads.retrieve(thread_id)
    thread = client.beta.threads.create()
    output = send_message(prompt, thread)
    
    return jsonify({ 'result': output })

@app.route('/message', methods=['POST'])
def openai2():
    data = request.get_json()
    prompt = data['prompt']
    thread_id = data['thread_id']
    
    # get content from 'instructions.txt' filke
    with open('instructions.txt', 'r') as file:
        doc = file.read()
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "Eres un asistente para estudiantes universitarios de la carrera de ingeniería de software en la universidad de las fuerzas armadas \"ESPE\". Responde las respuestas solo con una o dos oraciones. Solo utiliza el o los archivos adjuntos para responder, no agreges información adicional que no exista en el o los archivos adjuntos.  Utiliza las respuestas que mas se asemejen a la pregunta, si no encuentras la respuesta en los documentos adjuntos responde con \"Disculpa no tengo información sobre ese dato.\" \n\n documento adjunto: {0}".format(doc)},
            {"role": "user", "content": prompt}
        ]
    )
    
    message = completion.choices[0].message.content
    
    print(message)
    
    return jsonify({ 'result': message })


@app.route('/new', methods=['GET'])
def create_thread():
    #thread = await client.beta.threads.create()
    #return jsonify({ 'thread_id': thread.id })
    return jsonify({ 'thread_id': 0 })


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')