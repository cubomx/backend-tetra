from django.http import HttpResponse, JsonResponse
import pymongo
import requests
import json
from bson import json_util

client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']


# Create your views here.
def index(request):
    collection = db['agenda']
    event_details = collection.find()
 
    data = list(event_details)
    
    json_data = json_util.dumps(data)

    print(json_data)
    response = HttpResponse(json_data, content_type='application/json')
    return response


def addEvento(request):
    data = json.loads(request.body.decode('utf-8'))
    print(data)
    print(data['name'])

    json_data = json_util.dumps([{"foo": "bar"}])
    response = HttpResponse(json_data, content_type='application/json')
    return response

#client = pymongo.MongoClient('mongodb://root:example@localhost/tetra')




'''event = {
    "id_evento": "SV_20240607",
    "fecha": "2024-06-06"
}

collection.insert_one(event)
'''


