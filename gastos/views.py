from django.http import HttpResponse
from django.conf import settings
import pandas as pd
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import checkData, generateIDTicket, returnExcel, search, check_keys, searchWithProjection, updateData, archivo_anual, archivo_mensual, resumen_evento
from helpers.admin import verifyRole
from io import BytesIO

client =  pymongo.MongoClient(settings.DB['HOST'], settings.DB['PORT'], username=settings.DB['USER'], password=settings.DB['PASS'])
db = client[settings.DB['NAME']]
abonosTable = db['abonos']
agendaTable = db['agenda']
gastosTable = db['gastos']
projection = {"_id": False}


def addGasto(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)

    data = json.loads(request.body.decode('utf-8'))
    statusCode = 200
    expected_keys = ['day', 'month', 'year', 'concept', 'amount', 'buyer', 'invoice']
    types = {'date':str, 'concept':str, 'amount':[float,int], 'buyer':str, 'invoice':str, 'day':int, 'month':int, 'year':int, 'expense_type':str, 'provider':str}
    res = {}

    allowed_roles = {'admin', 'finance', 'vendor'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else:
        if not checkData(data, ['id_event'], {'id_event' : str})[0]:
            res['message'] = 'ID de evento no encontrado'
        else:
            id_event = data['id_event']
            del data['id_event']
            isDataCorrect, message  = checkData(data, expected_keys, types)
            if isDataCorrect:
                if checkData(data, ['quantity'], {'quantity':[float,int]})[0]:
                    data['unit_price'] = data['amount'] / data['quantity']
                
                month = '0' + str(data['month']) if data['month'] < 10 else str(data['month'])
                day = '0' + str(data['day']) if data['day'] < 10 else str(data['day'])
                date = day + month + str(data['year'])[2:]
                data['id_expense'] = generateIDTicket(date)
                res['message'] = message
                if id_event != 'GENERAL' and data['expense_type'] != 'Gastos Administrativos':
                    data['allocation'] = [{'id_event' : id_event}]
                if data['expense_type'] != 'Inventario':
                    if id_event != 'GENERAL':
                        # this is a general expense of a event
                        update_query = {"$push": {"expenses": {'id_expense':data['id_expense'], 'expense_type':data['expense_type']}}}
                        queryResponse = updateData(agendaTable, {'id_event': id_event}, update_query)
                    
                    result = gastosTable.insert_one(data)
                    if result.inserted_id:
                        res['message'] = 'Se agrego con exito el ticket {} al {}'.format(data['id_expense'], data['expense_type'])
                    else:
                        res['message'] = 'Hubo un error al agregar el ticket {} al {}'.format(data['id_expense'], data['expense_type'])
                else:
                    if id_event != 'GENERAL':
                        if search({'id_event' : id_event}, agendaTable):
                            data['available'] = 0
                            data['allocation'] = [{'id_event' : id_event}]
                            result = gastosTable.insert_one(data)
                            # Also, we need to add the reference of the allocation
                            update_query = {"$push": {"expenses": {'id_expense':data['id_expense'],'portion' : data['quantity'], 'expense_type':data['expense_type']}}}
                            queryResponse = updateData(agendaTable, {'id_event': id_event}, update_query)
                            if queryResponse['result'] > 0:
                                res['message'] = 'Se agrego con exito el ticket {} al evento {}'.format(data['id_expense'], id_event)
                            else:
                                res['message'] = 'Hubo un error al agregar el ticket {} al evento {}'.format(data['id_expense'], id_event)
                        else:
                            res['message'] = 'Evento no encontrado: {}'.format(id_event)
                            statusCode = 404
                    else:
                        data['available'] = data['quantity']
                        result = gastosTable.insert_one(data)
                        if result.inserted_id:
                            res['message'] = 'Se agrego con exito el ticket {} al {}'.format(data['id_expense'], data['expense_type'])
                        else:
                            res['message'] = 'Hubo un error al agregar el ticket {} al {}'.format(data['id_expense'], data['expense_type'])
            else:
                res['message'] = message
    
    
    json_data = json_util.dumps(res)
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response

def checkSearch(query, projection, table, errorMessage, successKey, failureKey):
    result, statusCode = searchWithProjection(query, projection, table, errorMessage)
    return (result, statusCode)

def getPayments(query):
    expenses = agendaTable.find_one(query, {"_id": 0,  "upfront":1})
    payments_ = list(abonosTable.find(query, {'_id':0,'quantity':1}).sort([("year", 1), ("month", 1), ("day", 1)]))

    payments = []
    payments.append(expenses['upfront'])
    for payment in payments_:
        payments.append(payment['quantity'])
    return payments

def contains_renta_and_salon(s):
    s_lower = s.lower()
    return 'renta' in s_lower and 'salon' in s_lower

def getCount(query):
    expenses = agendaTable.find_one(query, {"_id": 0, "expenses": 1, "cost":1, "upfront":1})
    payments = list(abonosTable.find(query, {'_id':0,'quantity':1}).sort([("year", 1), ("month", 1), ("day", 1)]))

    # Initialize a dictionary to store category totals
    totals = {'in':0, 'out':0, 'salon':0}


    totals['price'] = expenses['cost']

    for payment in payments:
        totals['in'] += payment['quantity']
    
    for expense in expenses['expenses']:
        id_expense = expense["id_expense"]
            
        # Find the corresponding expense in the second collection
        expense_details = gastosTable.find_one({"id_expense": id_expense})
        
        # If the expense is found
        if expense_details:
            amount = 0
            concept = expense_details["concept"]
            if contains_renta_and_salon(concept):
                totals['salon'] += expense_details["amount"]
                amount = expense_details["amount"]
            elif expense_details['expense_type'] == 'Inventary':
                unit_price = expense_details["unit_price"]
                portion = expense["portion"]
                
                # Calculate the amount
                amount = unit_price * portion
            else:
                amount = expense_details["amount"]
            
            # Update category total
            totals['out'] +=  amount
    return totals

def editGasto(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)

    payload = json.loads(request.body.decode('utf-8'))
    res = {}
    allowed_roles = {'admin'}
    result, statusCode = verifyRole(request, allowed_roles)
    expected_keys = ['day', 'month', 'year', 'concept', 'amount']
    types = {'day':int, 'month':int, 'year':int, 'concept':str, 'amount':[int,float], 'id_expense':str, 'expense_type':str}
    if statusCode != 200:
        res = result
    else:
        id_expense = payload['id_expense']
        if checkData(payload, expected_keys, types)[0]:
            expense_type = payload['expense_type']
            expense = gastosTable.find_one({'id_expense':id_expense}, {'_id':0})
            if not expense:
                res['message'] = 'Gasto no encontrado con ID {}'.format(id_expense)
            elif expense_type == 'Inventario':
                if  checkData(payload, ['quantity'], {'quantity':[int,float]})[0]:
                    if expense['quantity'] > payload['quantity']:
                        if checkData(expense, 'allocation', {'allocation':list})[0]:
                            # get all the assigned portions
                            id_events = []
                            for allocation in expense['allocation']:
                                id_events.append(allocation['id_event'])
                            pipeline = [
                                {
                                    '$match': { 'id_event': { '$in': id_events } }
                                },
                                {
                                    '$unwind': '$expenses'
                                },
                                {
                                    '$match': { 'expenses.id_expense': id_expense }
                                },
                                {
                                    '$project': { 'portion': '$expenses.portion' }
                                }
                            ]   

                            result = list(agendaTable.aggregate(pipeline))
                            totalPortion = 0
                            for assignment in result:
                                totalPortion += assignment['portion']
                            if totalPortion <= payload['quantity']:
                                diff = payload['quantity'] - expense['quantity'] 
                                resUpdate = updateData(gastosTable, {'id_expense':id_expense}, {'$set': payload, '$inc': {'available':diff}}) 
                                res = resUpdate 
                            else:
                                res['message'] = 'Se esta queriendo reducir a menos de lo ya asignado entre los multiples eventos'
                        else:
                            payload['available'] = payload['quantity']
                            print(payload)
                            resUpdate = updateData(gastosTable, {'id_expense':id_expense}, {'$set': payload}) 
                            res = resUpdate 
                    else:
                        diff = payload['quantity'] - expense['quantity'] 
                        resUpdate = updateData(gastosTable, {'id_expense':id_expense}, {'$set': payload, '$inc': {'available':diff}}) 
                        res = resUpdate 
                else:
                    del payload['quantity']
                    resUpdate =updateData(gastosTable, {'id_expense':id_expense}, {'$set': payload}) 
                    res = resUpdate 
            else:
                resUpdate =updateData(gastosTable, {'id_expense':id_expense}, {'$set': payload}) 
                res = resUpdate 
        else:
            res['message'] = 'Error al enviar los datos'
            statusCode = 400

    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)


def eliminar(table, payload):
    result = table.delete_one(payload)
    res = {}
    statusCode = 200
    if result.deleted_count > 0:
        res['message'] = f"Se elimino: {result.deleted_count} con exito"
    else:
        res['message'] = 'No se pudo eliminar'
        statusCode = 404
    return (res, statusCode)


def delGasto(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)

    payload = json.loads(request.body.decode('utf-8'))

    allowed_roles = {'admin'}
    res = {}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else:
        if checkData(payload, ['id_expense'], {'id_expense':str})[0]:
            id_expense = payload['id_expense']
            expense = gastosTable.find_one(payload, {'allocation':1, 'expense_type':1})
            res, statusCode = eliminar(gastosTable, payload)
            if statusCode == 200:
                if checkData(expense, ['allocation'], {'allocation':list})[0]:
                    print(expense)
                    for assignment in expense['allocation']:
                        id_event = assignment['id_event']
                        queryUpdateAgenda = {'$pull': {'expenses': {'id_expense':id_expense}}}
                        res_ = updateData(agendaTable, {'id_event':id_event}, queryUpdateAgenda) 
                        print(res_)

                res['message'] = 'Se elimino con exito'
            
        else:
            statusCode = 400
            res['message'] = 'Se enviaron mal los datos'


    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def getGasto(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)

    payload = json.loads(request.body.decode('utf-8'))
    res = {'expenses':[]}
    statusCode = 200
    
    allowed_roles = {'admin', 'auditor', 'finance', 'vendor', 'chef'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else: 
        if checkData(payload, ['expenses'], {'expenses' : dict})[0]:
            if checkData(payload['expenses'], ['id_event', 'expense_type'], {'id_event':str, 'expense_type':list})[0]:
                id_event = payload['expenses']['id_event']
                query = {'id_event': id_event}
                errorMessage = 'ERROR: Evento no encontrado {}'.format(id_event)
                result, statusCode = checkSearch(query, {'expenses': 1, "_id": 0}, agendaTable, errorMessage, 'expenses', 'message')
                if statusCode == 200:
                    for i in result:
                        for expense in i['expenses']:
                            if expense['expense_type'] in payload['expenses']['expense_type']:
                                id_expense = expense['id_expense']
                                query = {'id_expense':id_expense}
                                fields_excluded = ['_id','allocation', 'id_expense']
                                field_query = {field:0 for field in fields_excluded}
                                expense_data, newCode = checkSearch(query, field_query, gastosTable, 'Gasto no encontrado {}'.format(id_expense), 'expenses', 'message') 
                                if newCode == 200:
                                    for data in expense_data:
                                        expense.update(data)
                                # get the cost proportionated cost 
                                print(expense_data)
                                if checkData(expense_data[0], ['quantity'], {'quantity':[int,float]})[0]:
                                    print("hehehehheheheh")
                                    expense['amount'] = expense['portion'] * expense_data[0]['unit_price']
                                res['expenses'].append(expense)
                else:
                    res['message'] = result
            else:
                res['message'] = 'ID de evento no proporcionado'
                statusCode = 400
            
        elif checkData(payload, ['filters'], {'filters' : dict})[0]:
            result = None
            if check_keys(payload['filters'], ['day', 'month', 'year', 'concept', 'expense_type']):
                result, statusCode = checkSearch(payload['filters'], projection, gastosTable, 'ERROR: Gastos no encontrados', 'expenses', 'message')
            if statusCode == 200:
                res['expenses'] = result
            elif statusCode != 200:
                res = result[0]
        elif checkData(payload, ['id_event'], {'id_event':str})[0]:
            if agendaTable.find_one(payload):
                res['expenses'] = getCount(payload)
            else:
                res = {'message':'No se encontro el evento {}'.format(payload['id_event'])}
                statusCode = 404
        else:
            res['message'] = 'Falta la informacion "expenses"/"filters"'
            statusCode = 400
            
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def searchExpense(expenses, id_expense):
    for expense in expenses:
        print(expenses)
        if expense['id_expense'] == id_expense:
            return expense['portion']
    return -1

def searchInExpense(id_expense):
    fields_excluded = ['_id', 'day', 'month', 'year', 'concept', 'concept', 'buyer', 'id_expense']
    field_query = {field:0 for field in fields_excluded}
    expense, statusCode = searchWithProjection({'id_expense':id_expense}, field_query, gastosTable, 'Gasto no encontrado')
    return (expense, statusCode)

def checkExpenseAvailability(expense, portionDesire, portionOld, id_event, id_expense, queryUpdateGastos, queryUpdateAgenda, available, queryGastos, queryAgenda):
    res = {}
    statusCode = 200
    expense = expense[0]
    print(available + portionOld)
    if available + portionOld < portionDesire:
        res['message'] = 'La cantidad deseada {} es mayor a la disponible (o la disponible mas la que ya tienes asignada) {} del gasto seleccionado'.format(portionDesire, available + portionOld)
        statusCode = 404
    else:
        resultUpdateGastos = updateData(gastosTable, queryGastos, queryUpdateGastos)
        if resultUpdateGastos['result'] > 0:
            resultUpdateAgenda = updateData(agendaTable, queryAgenda, queryUpdateAgenda)
            if resultUpdateAgenda['result'] > 0:
                res['message'] = 'Se modifico con exito a la cantidad {} del gasto {} al evento {}'.format(portionDesire, id_expense, id_event)
            else:
                res['message'] = 'Hubo un error al querer alocar del gasto {} al evento {}'.format(id_expense, id_event)
                statusCode = 500
        else:
            res['message'] = 'Hubo un error al querer alocar del gasto {} al evento {}'.format(id_expense, id_event)
            statusCode = 500
    return (res, statusCode)

def modifyGasto(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    res = {}
    statusCode = 200
    allowed_roles = {'admin', 'chef'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    elif checkData(data, ['id_event', 'id_expense', 'portion'], {'id_event' : str, 'id_expense' : str, 'portion':[int,float]})[0]:
        #res['message'] = 'Correcta la data'
        id_event = data['id_event']
        id_expense = data['id_expense']
        portionDesire = data['portion']
        event = search({'id_event': id_event}, agendaTable)
        statusCode = 200
        
        if event:
            portion = searchExpense(event[0]['expenses'], id_expense)
            if portion == -1:
                if portionDesire <= 0.0:
                    statusCode = 400
                    res['message'] = 'Has pedido 0 del gasto {}, no es posible asignar nulo'
                else:
                    print('No encontramos el gasto deseado {} en el evento buscado: {}'.format(id_event, id_expense))
                    expense, statusCode = searchInExpense(id_expense)
                    if statusCode == 200:
                        expense_type = expense[0]['expense_type']
                        available = expense[0]['available']
                        newAvailable = available - portionDesire
                        queryUpdateGastos = {'$push': {'allocation': {'id_event':id_event}}, '$set': {'available': newAvailable}}
                        queryUpdateAgenda = {'$push': {'expenses': {'id_expense':id_expense,'portion' : portionDesire, 'expense_type': expense[0]['expense_type']}}}
                        res, statusCode = checkExpenseAvailability(expense, portionDesire, 0,  id_event, id_expense, 
                            queryUpdateGastos, queryUpdateAgenda, available, {'id_expense': id_expense}, {'id_event': id_event})
                    else:
                        res['message'] = 'No encontramos el gasto deseado {} para el evento'.format(id_expense, id_event)
                        statusCode = 404
            else:
                
                diff = portion - portionDesire
                expense, statusCode = searchInExpense(id_expense)
                available = expense[0]['available']
                newAvailable = 0

                newAvailable = available + diff 
                if diff == 0.0:
                    res['message'] = 'Estas asignando lo mismo, no hay cambio alguno'

                elif diff < 0.0 and available < diff:
                    res['message'] = 'La cantidad deseada {} es mayor a la disponible {} del gasto seleccionado'.format(portionDesire, available)
                    statusCode = 400

                elif portionDesire <= 0.0:
                    # search if exist available
                    queryUpdateGastos = {'$set': {'available': newAvailable}, '$pull' : {'allocation':{'id_event':id_event}}}
                    queryUpdateAgenda = {'$pull': {'expenses': {'id_expense':id_expense}}}
                    res, statusCode = checkExpenseAvailability(expense, portionDesire, portion, id_event, id_expense, queryUpdateGastos, 
                        queryUpdateAgenda, newAvailable, {'id_expense':id_expense}, {'id_event':id_event, "expenses.id_expense":id_expense})

                else:
                    queryUpdateGastos = {'$set': {'available': newAvailable}}
                    queryUpdateAgenda = {'$set': {'expenses.$.portion': portionDesire}}
                    res, statusCode = checkExpenseAvailability(expense, portionDesire, portion, id_event, id_expense, queryUpdateGastos, 
                        queryUpdateAgenda, available, {'id_expense':id_expense}, {'id_event':id_event, "expenses.id_expense":id_expense})

        else:
            res['message'] = 'No encontramos el evento deseado: {}'.format(id_event)
            statusCode = 404
    else:
        res['message'] = 'Parece que falta un dato por enviar: id_event, id_expense, portion'
        statusCode = 400
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def guardarEstadoResultados(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    res = {}
    statusCode = 200
    allowed_roles = {'admin', 'finance'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    elif checkData(data, ['id_event','in', 'out','margin','utility'],
        {'id_event':str, 'payments':list, 'in':[int,float], 'out':[int,float], 'margin':[int,float], 'salonPrice':[int,float],'utility':[int,float]})[0]:
            if agendaTable.find_one({'id_event': data['id_event']}):
                id_event = data['id_event'] 
                del data['id_event']
                updateData(agendaTable, {'id_event': id_event}, {'$set' : {'state':'completado', 'margin': data}})
                res['message'] = 'Se concluyo con exito'
            else:
                statusCode = 400
                res['message'] = 'No se encontro el evento {}'.format(data['id_event'])
    else:
        res['message'] = 'Falto informacion por enviar'

    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def revertirMargenResultados(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    res = {}
    statusCode = 200
    allowed_roles = {'admin', 'finance'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    elif checkData(data, ['id_event'], {'id_event':str})[0]:
        print('hehe')
        if agendaTable.find_one({'id_event':data['id_event'], 'state':'completado'}):
            updateData(agendaTable, {'id_event':data['id_event'], 'state':'completado'}, 
                       {'$set' : {'state':'pendiente'}, '$unset': {'margin': ''}})
            res['message'] = 'Se revirtio con exito el evento'
        else:
            res['message'] = 'Evento no encontrado'
            statusCode = 404
    else:
        res['message'] = 'No se envio el id del evento'
        statusCode = 400
    print(data)
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def fixData(data):
    final_result = {}
    for key, value in data['margin'].items():
        if key == 'margin':
            final_result['margin'] = value
        else:
            final_result[key] = value
    return final_result


def getMargenResultados(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    res = {}
    statusCode = 200
    allowed_roles = {'admin', 'auditor', 'finance'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    elif checkData(data, ['id_event'], {'id_event':str})[0]:
        print(data['id_event'])
        id_event = data['id_event']
        result = agendaTable.find_one({'id_event':id_event, 'state':'completado'}, {'_id':0})      
        if result:
            pipeline = [
                {
                    "$match": {"id_event": id_event}
                },
                {
                    "$addFields": {
                        "date": {
                            "$concat": [
                                {"$cond": {"if": {"$lt": ["$day", 10]}, "then": {"$concat": ["0", {"$toString": "$day"}]}, "else": {"$toString": "$day"}}},
                                "/",
                                {"$cond": {"if": {"$lt": ["$month", 10]}, "then": {"$concat": ["0", {"$toString": "$month"}]}, "else": {"$toString": "$month"}}},
                                "/",
                                {"$toString": "$year"}
                            ]
                        }
                    }
                },
                {
                        "$project": {
                            "_id": 0, "_id_event": 0,"day": 0,"month": 0, "year": 0}
                    }
                ]

            ingresos = list(abonosTable.aggregate(pipeline))
            egresos = []
            inventario = []
            result['date'] = str(result['day']) + '/' + str(result['month']) +  '/' + str(result['year'])
            result.update(fixData(result))
            [result.pop(key) for key in ['day', 'month', 'year'] if key in result]
            for expense in result['expenses']:
                ex = expense
                id_expense = ex['id_expense']
                # search for the expense details
                expense_details = gastosTable.find_one({"id_expense": id_expense}, {'_id':0, '_id_event':0, 'allocation':0, 'id_expense':0, 'available':0})
                expense_type = expense_details['expense_type']
                del ex['expense_type']
                del ex['id_expense']
                del expense_details['expense_type']
                print(expense_type)
                if expense_type == 'Inventario':
                    unit_price = expense_details["unit_price"]
                    del expense_details["unit_price"]
                    portion = ex["portion"]
                    expense_details['date'] = str(expense_details['day']) + '/' + str(expense_details['month']) + '/' + str(expense_details['year'])
                    # Calculate the amount
                    amount = unit_price * portion
                    expense_details['amount'] = amount
                    [expense_details.pop(key) for key in ['day', 'month', 'year'] if key in expense_details]
                    ex.update(expense_details)
                    inventario.append(ex)
                else:
                    expense_details['date'] = str(expense_details['day']) + '/' + str(expense_details['month']) + '/' + str(expense_details['year'])
                    [expense_details.pop(key) for key in ['day', 'month', 'year'] if key in expense_details]
                    ex.update(expense_details)
                    egresos.append(ex)
            del result['expenses']
            wb = resumen_evento(result, egresos, ingresos, inventario)
            
            return returnExcel(wb, 'resumen_evento')
        else:
            statusCode = 404
            res['message'] - 'No se encontro el evento'
    else:
        res['message'] = 'No se envio el id del evento'
        statusCode = 400
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)


def pipeline(field, match):
    pipeline = [
        {
            '$match': match
        },
        {
            '$group': {
                '_id': None,  # We do not want to group by any specific field, hence None
                'total_sum': {'$sum': f'${field}'}
            }
        }
    ]
    return pipeline


def getTotales(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    res = {}
    statusCode = 200
    allowed_roles = {'admin', 'finance'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    elif check_keys(data, ['day', 'month', 'year']):
        total_gasto = list(gastosTable.aggregate(pipeline('amount', data)))
        total_ingreso = list(abonosTable.aggregate(pipeline('quantity', data)))
        totales = {}
        totales['egresos'] = (total_gasto[0]['total_sum']) if len(total_gasto) > 0  else 0
        totales['ingresos'] = (total_ingreso[0]['total_sum']) if len(total_ingreso) > 0  else 0

        res['totales'] = totales
    else:
        res['message'] = 'No se envio la fecha'
        statusCode = 400
    print(data)
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def getEventData(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    res = {}
    statusCode = 200
    allowed_roles = {'admin', 'auditor', 'finance', 'vendor', 'chef'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    elif checkData(data, ['id_event'], {'id_event':str})[0]:
        event = agendaTable.find_one({'id_event': data['id_event']}, projection)
        print(event)
        if event:
            dta = {}
            res['data'] = []
            egresses = getCount(data)
            del egresses['price']
            del egresses['payments']

            total_egresses = 0
            for value in egresses.values():
                total_egresses += value
            
            total_ingreso = list(abonosTable.aggregate(pipeline('quantity', data)))

            
            dta['ingresses'] = (total_ingreso[0]['total_sum']) if len(total_ingreso) > 0  else 0
            dta['egresses'] = total_egresses
            dta.update(event)
            dta.update(egresses)
            res['data'] = dta
        else:
            res['message'] = 'No se encontro el evento {}'.format(data['id_event'])
            statusCode = 404

    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def matchExpense(match):
    pipeline = [
                    {
                        '$match': match
                    },
                    {
                        '$group': {
                            '_id': {
                                'month': '$month',
                                'concept': '$concept'
                            },
                            'totalQuantity': {
                                '$sum': '$amount'
                            }
                        }
                    },
                    {
                        '$project': {
                            '_id': 0,
                            'month': '$_id.month',
                            'concept': '$_id.concept',
                            'totalQuantity': 1
                        }
                    }
                ]
    return pipeline

def getResumen(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    res = {}
    statusCode = 200
    allowed_roles = {'admin', 'auditor', 'finance'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    elif checkData(data, ['year'], {'year':int})[0]:
        if checkData(data, ['month'], {'month':int})[0]:
            '''pipeline = [
                {
                    '$match': {
                        'year': year,
                        'month': month
                    }
                },
                {
                    '$group': {
                        '_id': {
                            'concept': '$concept'
                        },
                        'totalQuantity': {
                            '$sum': '$quantity'
                        }
                    }
                },
                {
                    '$project': {
                        '_id': 0,
                        'concept': '$_id.concept',
                        'totalQuantity': 1
                    }
                }
            ]

            
            ingresos = list(abonosTable.aggregate(pipeline))
            inventario = list(gastosTable.aggregate(matchExpense({'year': year, 'month':month, 'expense_type':'Inventario'})))'''
            pipeline = [
                {
                    "$match": data
                },
                {
                    "$addFields": {
                        "date": {
                            "$concat": [
                                {"$cond": {"if": {"$lt": ["$day", 10]}, "then": {"$concat": ["0", {"$toString": "$day"}]}, "else": {"$toString": "$day"}}},
                                "/",
                                {"$cond": {"if": {"$lt": ["$month", 10]}, "then": {"$concat": ["0", {"$toString": "$month"}]}, "else": {"$toString": "$month"}}},
                                "/",
                                {"$toString": "$year"}
                            ]
                        }
                    }
                },
                {
                        "$project": {
                            "_id": 0,"day": 0,"month": 0, "year": 0, 'allocation':0, 'available':0, 'unit_price':0,  'quantity':0, 'id_expense':0}
                    }
                ]
            gastos = list(gastosTable.aggregate(pipeline))
            print(gastos)
            header_translation = {
                'buyer': 'Comprador',
                'concept': 'Concepto',
                'invoice': 'Folio',
                'provider': 'Proveedor',
                'expense_type': 'Tipo de Gasto',
                'amount': 'Monto',
                'date': 'Fecha'
            }
            wb = archivo_mensual(gastos, header_translation)
            return returnExcel(wb, 'resumen_mensual')
        else:
            year = data['year']
            pipeline = [
                {
                    '$match': {'year': year}},
                {
                    '$group': {
                        '_id': {
                            'month': '$month',
                            'concept': '$concept'
                        },
                        'totalQuantity': {
                            '$sum': '$quantity'
                        }
                    }
                },
                {
                    '$project': {
                        '_id': 0,
                        'month': '$_id.month',
                        'concept': '$_id.concept',
                        'totalQuantity': 1
                    }
                }
            ]

            

            ingresos = list(abonosTable.aggregate(pipeline))
            inventario = list(gastosTable.aggregate(matchExpense({'year': year, 'expense_type':'Inventario'})))
            gastos = list(gastosTable.aggregate(matchExpense({'year': year, 'expense_type':'Gastos'})))
            gastos_gen = list(gastosTable.aggregate(matchExpense({'year': year, 'expense_type':'Gastos Administrativos'})))

            wb = archivo_anual(ingresos, gastos, inventario, gastos_gen)
            return returnExcel(wb, 'resumen_anual')
    else:
        res['message'] = 'No se encontro los campos month, year'
        statusCode = 404

    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)
