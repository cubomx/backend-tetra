from django.http import HttpResponse
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import checkData, search, generateTicketNumber, getDate

client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']


def addAbono(request):
    abonosTable = db['abonos']
    agendaTable = db['agenda']
    data = json.loads(request.body.decode('utf-8'))
    keys = ['id_evento', 'quantity', 'payer']

    isDataCorrect, message = checkData(data, keys)


    if isDataCorrect:
        id_evento = data['id_evento']
        query = {"id_evento": id_evento}
        eventFound = search(query, agendaTable)
        if eventFound:
           print('Found event with id_evento {}'.format(id_evento))
           id_ticket = generateTicketNumber(4, getDate())
           print('Ticket ID Number: {}'.format(id_ticket))
           data['id_ticket'] = id_ticket

           res = abonosTable.insert_one(data)
           status = "successful. Ticket ID {}".format(id_ticket) if res.inserted_id  else "failed."   
           message = 'Ticket added {}'.format(status)
        else:
            message = 'Missing event by id_evento'

    
    json_data = json_util.dumps([{"message": message}])
    response = HttpResponse(json_data, content_type='application/json')
    return response