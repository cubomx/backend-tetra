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
    keys = ['id_evento', 'quantity', 'payer']

    statusCode = 200
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
           data['day'], data['month'], data['year']  = [int(x) for x in getDate().split('-')]
    
           res = abonosTable.insert_one(data)
           
           if res.inserted_id:
               status = "successful. Ticket ID {}".format(id_ticket)
           else:
               status = "failed." 
               statusCode = 404
           message = 'Ticket added {}'.format(status)
        else:
            message = 'Missing event by id_evento'
            statusCode = 400


    
    json_data = json_util.dumps([{"message": message}])
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response



def getAbono(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')
    
    data = json.loads(request.body.decode('utf-8'))
    status = 200
    expected_keys = ['id_evento', 'id_ticket']
    res = {}
    # check by ids
    if check_keys(data, expected_keys):
        result, status = findAbono(data, abonosTable)
        if status != 200: 
            res = result
            print("hei")
        else:
            res['payments'] = result
    # check by date
    
    elif checkData(data, ['type'])[0]:
        data = deleteExtraQueries(data, ['type', 'day', 'month'])
        id_eventos, status = searchWithProjection({'type' : data['type']}, {"_id": 0, "id_evento": 1}, agendaTable)
        del data['type']
        
        results = []
        for id_evento in id_eventos:
            query = data  | id_evento
            result = findAbono(query, abonosTable)[0]
            if result:
                for doc in result:
                    results.append(dict(doc))
        res = {'payments' : results}
 
    elif check_keys(data, ['day', 'month']):
        res['payments'], status = findAbono(data, abonosTable)
    else:
        res = {'message':'ERROR. We expect id_evento or id_ticket (or both) in the JSON request. Or, by day, month, type'}
        status = 400
    return HttpResponse([res], content_type='application/json', status=status)

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
            message = 'Event deleted successfully.'
        else:
            message = 'Payment not found or wrong id_ticket'
            status = 404
    else:
        message = 'Not id_ticket in JSON'
        status = 400
    json_data = json_util.dumps([{"message": message}])
    
    return HttpResponse(json_data, content_type='application/json', status=status)
