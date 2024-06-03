from django.http import HttpResponse
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import checkData, search, generateTicketNumber, getDate, check_keys, searchWithProjection, findAbono, deleteExtraQueries
from helpers.admin import verifyRole
import datetime
import pytz

client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']
abonosTable = db['abonos']
agendaTable = db['agenda']


def addAbono(request): 
    data = json.loads(request.body.decode('utf-8'))
    keys = ['id_event', 'quantity', 'payer']
    types = {'id_event' : str, 'quantity' : [float, int], 'payer' : [str]}

    statusCode = 200
    isDataCorrect, message = checkData(data, keys, types)
    res={}

    allowed_roles = {'admin', 'finance'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    elif isDataCorrect:
        id_event = data['id_event']
        query = {"id_event": id_event}
        eventFound = search(query, agendaTable)
        if eventFound:
           
           print('Found event with id_event {}'.format(id_event))
           id_ticket = generateTicketNumber(getDate())
           print('Ticket ID Number: {}'.format(id_ticket))
           # Define the time zone you want to work with
           tz = pytz.timezone('America/Mexico_City')  # Example: Eastern Time Zone

            # Get the current date and time in the specified time zone
           current_time = datetime.datetime.now(tz)

            # Format the date and time
           formatted_time = current_time.strftime('%d-%m-%Y')

           data['id_ticket'] = id_ticket
           data['day'], data['month'], data['year']  = [int(x) for x in formatted_time.split('-')]
    
           result = abonosTable.insert_one(data)
           
           if result.inserted_id:
               status = "satisfactoriamente. Ticket ID {}".format(id_ticket)
           else:
               status = "fallido." 
               statusCode = 404
           res['message'] = 'Ticket agregado {}'.format(status)
        else:
            res['message'] = 'No se encontro el evento por el ID: {}'.format(data['id_event'])
            statusCode = 400
    else:
        res['message'] = message 
        statusCode = 400


    
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def getAbono(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')
    
    data = json.loads(request.body.decode('utf-8'))
    statusCode = 200
    expected_keys = ['id_event', 'id_ticket']
    res = {}

    allowed_roles = {'admin', 'finance', 'inventary', 'secretary'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else:
        if check_keys(data, expected_keys):
            result, statusCode = findAbono(data, abonosTable)
            if statusCode != 200: 
                res['payments'] = []
                statusCode = 200
            else:
                res['payments'] = result
        elif checkData(data, ['type'], {'type' : str })[0]:
            data = deleteExtraQueries(data, ['type', 'day', 'month'])
            id_events, statusCode = searchWithProjection({'type' : data['type']}, {"_id": 0, "id_event": 1}, agendaTable, 'ERROR. Payment not found')
            del data['type']
            results = []
            for id_event in id_events:
                query = data  | id_event
                result = findAbono(query, abonosTable)[0]
                if result:
                    for doc in result:
                        results.append(dict(doc))
            res = {'payments' : results}
    
        elif check_keys(data, ['day', 'month', 'year']):
            res['payments'], statusCode = findAbono(data, abonosTable)
            if statusCode == 200:
                for idx, payment in enumerate(res['payments']):
                    id_event = payment['id_event']
                    event = agendaTable.find_one({'id_event':id_event}, {'type': 1, 'name': 1, 'location':1, '_id':0})
                    res['payments'][idx].update(event)
            else:
                res['message'] = res['payments']['message']
                del res['payments']
        else:
            res = {'message':'ERROR. Se espera el ID del evento o del ticket (o ambos) en la petición JSON. O, por "day", "month", "type"'}
            statusCode = 400
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def delAbono(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')

    data = json.loads(request.body.decode('utf-8'))
    keys = ['id_ticket']
    
    isDataCorrect = check_keys(data, keys)
    status = 200

    allowed_roles = {'admin', 'finance'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    elif isDataCorrect:
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
