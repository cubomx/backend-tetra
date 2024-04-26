from django.http import HttpResponse
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import checkData, search

client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']
abonosTable = db['abonos']
agendaTable = db['agenda']
comprasTable = db['compras']
inventarioTable = db['inventario']


def addCompra(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')

    data = json.loads(request.body.decode('utf-8'))
    statusCode = 400
    expected_keys = ['id_event', 'date', 'concept', 'amount', 'buyer', 'quantity']
    types = {'id_event' : str, 'date' : str, 'concept' : str, 'amount' : float, 'buyer' : str, 
             'quantity' : float}
    res = {}

    if not checkData(data, ['id_event'], {'id_event' : str})[0]:
        res['message'] = 'Missing id_event'
    else:
        isDataCorrect, message  = checkData(data, expected_keys, types)
        if isDataCorrect:
            unit_price = data['amount'] / data['quantity']
            data['unit_price'] = unit_price
            res['message'] = message
            if data['id_event'] == 'GENERAL':
                inventarioTable.insert_one(data)
            else:
                if search({'id_event' : data['id_event']}, agendaTable):
                    res['message'] = 'FOUND'
                    statusCode = 200
                else:
                    res['message'] = 'Event not found by id_event {}'.format(data['id_event'])
                    statusCode = 200
        else:
            res['message'] = message
    

    json_data = json_util.dumps([res])
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response