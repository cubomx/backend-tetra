from django.http import HttpResponse
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import checkData, search, generateTicketNumber, getDate, check_keys, searchWithProjection, findAbono, deleteExtraQueries

client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']
abonosTable = db['abonos']
agendaTable = db['agenda']


def addAbono(request): 
    data = json.loads(request.body.decode('utf-8'))
    keys = ['id_event', 'quantity', 'payer']
    types = {'id_event' : str, 'quantity' : float, 'payer' : str}

    statusCode = 200
    isDataCorrect, message = checkData(data, keys, types)

    if isDataCorrect:
        id_event = data['id_event']
        query = {"id_event": id_event}
        eventFound = search(query, agendaTable)
        if eventFound:
           print('Found event with id_event {}'.format(id_event))
           id_ticket = generateTicketNumber(4, getDate())
           print('Ticket ID Number: {}'.format(id_ticket))
           data['id_ticket'] = id_ticket
           data['day'], data['month'], data['year']  = [int(x) for x in getDate().split('-')]
    
           res = abonosTable.insert_one(data)
           
           if res.inserted_id:
               status = "satisfactoriamente. Ticket ID {}".format(id_ticket)
           else:
               status = "fallido." 
               statusCode = 404
           message = 'Ticket agregado {}'.format(status)
        else:
            message = 'No se encontro el evento por el ID: {}'.format(data['id_event'])
            statusCode = 400


    
    json_data = json_util.dumps([{"message": message}])
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response



def getAbono(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')
    
    data = json.loads(request.body.decode('utf-8'))
    status = 200
    expected_keys = ['id_event', 'id_ticket']
    res = {}
    # check by ids
    if check_keys(data, expected_keys):
        result, status = findAbono(data, abonosTable)
        if status != 200: 
            res = result
        else:
            res['payments'] = result
    # check by date
    
    elif checkData(data, ['type'], {'type' : str })[0]:
        data = deleteExtraQueries(data, ['type', 'day', 'month'])
        id_events, status = searchWithProjection({'type' : data['type']}, {"_id": 0, "id_event": 1}, agendaTable, 'ERROR. Payment not found')
        del data['type']
        
        results = []
        for id_event in id_events:
            query = data  | id_event
            result = findAbono(query, abonosTable)[0]
            if result:
                for doc in result:
                    results.append(dict(doc))
        res = {'payments' : results}
 
    elif check_keys(data, ['day', 'month']):
        res['payments'], status = findAbono(data, abonosTable)
    else:
        res = {'message':'ERROR. Se espera el ID del evento o del ticket (o ambos) en la petición JSON. O, por "day", "month", "type"'}
        status = 400
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=status)

def delAbono(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')

    data = json.loads(request.body.decode('utf-8'))
    keys = ['id_ticket']
    
    isDataCorrect = check_keys(data, keys)
    status = 200

    if isDataCorrect:
        res = abonosTable.delete_one(data)

        # Check if the deletion was successful
        if res.deleted_count == 1:
            message = 'Abono eliminado satisfactoriamente.'
        else:
            message = 'Abono no encontrado o ID de ticket equivocado'
            status = 404
    else:
        message = 'No ID de ticket en JSON'
        status = 400
    json_data = json_util.dumps([{"message": message}])
    
    return HttpResponse(json_data, content_type='application/json', status=status)
