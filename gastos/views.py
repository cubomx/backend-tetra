from django.http import HttpResponse
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import checkData, generateIDTicket, search, check_keys, searchWithProjection, updateData

client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']
abonosTable = db['abonos']
agendaTable = db['agenda']
gastosTable = db['gastos']
projection = {"_id": False}


def addGasto(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')

    data = json.loads(request.body.decode('utf-8'))
    statusCode = 200
    expected_keys = ['day', 'month', 'year', 'concept', 'amount', 'buyer', 'quantity', 'category']
    types = {'id_event':str, 'date':str, 'concept':str, 'amount':float, 'buyer':str, 
             'quantity':float, 'category':str, 'day':int, 'month':int, 'year':int, 'expense_type':str}
    res = {}
    result = None

    if not checkData(data, ['id_event'], {'id_event' : str})[0]:
        res['message'] = 'ID de evento no encontrado'
    else:
        id_event = data['id_event']
        del data['id_event']
        isDataCorrect, message  = checkData(data, expected_keys, types)
        if isDataCorrect:
            unit_price = data['amount'] / data['quantity']
            data['unit_price'] = unit_price
            date = str(data['day']) + str(data['month']) + str(data['year'])
            data['id_expense'] = generateIDTicket(4, date)
            res['message'] = message
            if id_event == 'GENERAL':
                data['available'] = data['quantity']
                result = gastosTable.insert_one(data)
            else:
                if search({'id_event' : id_event}, agendaTable):
                    
                    data['available'] = 0
                    data['allocation'] = [{'id_event' : id_event}]
                    res['message'] = 'FOUND'
                    result = gastosTable.insert_one(data)
                    # Also, we need to add the reference of the allocation
                    update_query = {"$push": {"expenses": {'id_expense':data['id_expense'],'portion' : data['quantity']}}}
                    queryResponse = updateData(agendaTable, {'id_event': id_event}, update_query)
                    if queryResponse['result'] > 0:
                        print('Se agregó con éxito el ticket {} al evento {}'.format(data['id_expense'], id_event))
                    else:
                        print('Hubo un error al añadir el ticket {} al evento {}'.format(data['id_expense'], id_event))
                else:
                    res['message'] = 'Evento no encontrado: {}'.format(id_event)
                    statusCode = 404
            if result != None and result.inserted_id:
               status = "con éxito. Ticket ID {}".format(data['id_expense'])
            else:
               status = "fallido." 
               statusCode = 404
            res['message'] = 'Gasto añadido {}'.format(status)
        else:
            res['message'] = message
    

    json_data = json_util.dumps([res])
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response

def checkSearch(query, projection, table, errorMessage, successKey, failureKey):
    result, statusCode = searchWithProjection(query, projection, table, errorMessage)
    return (result, statusCode)
    

def getGasto(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')

    data = json.loads(request.body.decode('utf-8'))
    res = {'expenses':[]}
    statusCode = 200
    
    if checkData(data, ['expenses'], {'expenses' : dict})[0]:
        if checkData(data['expenses'], ['id_event'], {'id_event':str})[0]:
            id_event = data['expenses']['id_event']
            query = {'id_event': id_event}
            errorMessage = 'ERROR: Evento no encontrado {}'.format(id_event)
            result, statusCode = checkSearch(query, {'expenses': 1, "_id": 0}, agendaTable, errorMessage, 'expenses', 'message')
            if statusCode == 200:
                for i in result:
                    for expense in i['expenses']:
                        print(expense)
                        res['expenses'].append(expense)
        else:
            res['message'] = 'ID de evento no proporcionado'
            statusCode = 400
        
    elif checkData(data, ['filters'], {'filters' : dict})[0]:

        if check_keys(data['filters'], ['day', 'month', 'year', 'category', 'expense_type']):
            res, statusCode = checkSearch(data['filters'], projection, gastosTable, 'ERROR: Gastos no encontrados', 'expenses', 'message')
    else:
        res['message'] = 'Falta la informacion "expenses"/"filters"'
        statusCode = 400
            
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)
    