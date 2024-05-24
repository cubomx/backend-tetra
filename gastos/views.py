from django.http import HttpResponse
import pandas as pd
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import checkData, generateIDTicket, returnExcel, search, check_keys, searchWithProjection, updateData
from helpers.admin import verifyRole

client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']
abonosTable = db['abonos']
agendaTable = db['agenda']
gastosTable = db['gastos']
projection = {"_id": False}


def addGasto(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)

    data = json.loads(request.body.decode('utf-8'))
    statusCode = 200
    expected_keys = ['day', 'month', 'year', 'concept', 'amount', 'buyer', 'quantity', 'category']
    types = {'date':str, 'concept':str, 'amount':[float,int], 'buyer':str, 
             'quantity':[float, int], 'category':str, 'day':int, 'month':int, 'year':int, 'expense_type':str}
    res = {}

    allowed_roles = {'admin', 'finance'}
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
                unit_price = data['amount'] / data['quantity']
                data['unit_price'] = unit_price
                date = str(data['day']) + str(data['month']) + str(data['year'])
                data['id_expense'] = generateIDTicket(4, date)
                res['message'] = message
                if id_event == 'GENERAL':
                    data['available'] = data['quantity']
                    result = gastosTable.insert_one(data)
                    if result.inserted_id:
                        res['message'] = 'Se agrego con exito el ticket {} al {}'.format(data['id_expense'], data['expense_type'])
                    else:
                        res['message'] = 'Hubo un error al agregar el ticket {} al {}'.format(data['id_expense'], data['expense_type'])
                else:
                    if search({'id_event' : id_event}, agendaTable):
                        data['available'] = 0
                        data['allocation'] = [{'id_event' : id_event}]
                        result = gastosTable.insert_one(data)
                        # Also, we need to add the reference of the allocation
                        update_query = {"$push": {"expenses": {'id_expense':data['id_expense'],'portion' : data['quantity']}}}
                        queryResponse = updateData(agendaTable, {'id_event': id_event}, update_query)
                        if queryResponse['result'] > 0:
                            res['message'] = 'Se agrego con exito el ticket {} al evento {}'.format(data['id_expense'], id_event)
                        else:
                            res['message'] = 'Hubo un error al agregar el ticket {} al evento {}'.format(data['id_expense'], id_event)
                    else:
                        res['message'] = 'Evento no encontrado: {}'.format(id_event)
                        statusCode = 404
            else:
                res['message'] = message
    
    
    json_data = json_util.dumps(res)
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response

def checkSearch(query, projection, table, errorMessage, successKey, failureKey):
    result, statusCode = searchWithProjection(query, projection, table, errorMessage)
    return (result, statusCode)

def getPayments(query):
    expenses = agendaTable.find_one(query, {"_id": 0, "expenses": 1, "cost":1, "upfront":1})
    payments_ = list(abonosTable.find(query, {'_id':0,'quantity':1}).sort([("year", 1), ("month", 1), ("day", 1)]))

    payments = []
    payments.append(expenses['upfront'])
    for payment in payments_:
        payments.append(payment['quantity'])
    return payments

def getCount(query, categories, categoriesInEN):
    expenses = agendaTable.find_one(query, {"_id": 0, "expenses": 1, "cost":1, "upfront":1})
    payments = list(abonosTable.find(query, {'_id':0,'quantity':1}).sort([("year", 1), ("month", 1), ("day", 1)]))

    # Initialize a dictionary to store category totals
    totals = {}
    for category in categories:
        totals[categoriesInEN[category]] = 0

    totals['payments'] = []

    totals['price'] = expenses['cost']
    totals['payments'].append(expenses['upfront'])

    for payment in payments:
        totals['payments'].append(payment['quantity'])
    
    for expense in expenses['expenses']:
        id_expense = expense["id_expense"]
            
        # Find the corresponding expense in the second collection
        expense_details = gastosTable.find_one({"id_expense": id_expense})
        
        # If the expense is found
        if expense_details:
            category = expense_details["category"]
            unit_price = expense_details["unit_price"]
            portion = expense["portion"]
            
            # Calculate the amount
            amount = unit_price * portion
            
            # Update category total
            totals[categoriesInEN[category]] = totals.get(categoriesInEN[category], 0) + amount
    return totals
    

def getGasto(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)

    data = json.loads(request.body.decode('utf-8'))
    res = {'expenses':[]}
    statusCode = 200
    
    allowed_roles = {'admin', 'finance', 'inventary', 'secretary'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else: 
        if checkData(data, ['expenses'], {'expenses' : dict})[0]:
            if checkData(data['expenses'], ['id_event'], {'id_event':str})[0]:
                id_event = data['expenses']['id_event']
                query = {'id_event': id_event}
                errorMessage = 'ERROR: Evento no encontrado {}'.format(id_event)
                result, statusCode = checkSearch(query, {'expenses': 1, "_id": 0}, agendaTable, errorMessage, 'expenses', 'message')
                if statusCode == 200:
                    for i in result:
                        for expense in i['expenses']:
                            id_expense = expense['id_expense']
                            print(id_expense)
                            query = {'id_expense':id_expense}
                            fields_excluded = ['_id','quantity', 'allocation', 'available', 'id_expense', 'amount']
                            field_query = {field:0 for field in fields_excluded}
                            expense_data, newCode = checkSearch(query, field_query, gastosTable, 'Gasto no encontrado {}'.format(id_expense), 'expenses', 'message') 
                            if newCode == 200:
                                for data in expense_data:
                                    expense.update(data)
                            # get the cost proportionated cost 
                            expense['amount'] = expense['portion'] * expense['unit_price']
                            res['expenses'].append(expense)
                else:
                    res['message'] = result
            else:
                res['message'] = 'ID de evento no proporcionado'
                statusCode = 400
            
        elif checkData(data, ['filters'], {'filters' : dict})[0]:
            result = None
            if check_keys(data['filters'], ['day', 'month', 'year', 'category', 'expense_type']):
                result, statusCode = checkSearch(data['filters'], projection, gastosTable, 'ERROR: Gastos no encontrados', 'expenses', 'message')
            if statusCode == 200:
                res['expenses'] = result
            elif statusCode != 200:
                res = result[0]
        elif checkData(data, ['id_event'], {'id_event':str})[0]:
            if agendaTable.find_one(data):
                res['expenses'] = getCount(data, ['Alimentos', 'Bebidas', 'Salarios', 'Otros'], {'Alimentos':'food', 'Bebidas':'beverages','Salarios':'salaries','Otros':'others'})
            else:
                res = {'message':'No se encontro el evento {}'.format(data['id_event'])}
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
    fields_excluded = ['_id', 'day', 'month', 'year', 'concept', 'category', 'expense_type', 'buyer', 'id_expense']
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
    allowed_roles = {'admin', 'finance'}
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
            print(event)
            portion = searchExpense(event[0]['expenses'], id_expense)
            if portion == -1:
                if portionDesire <= 0.0:
                    statusCode = 400
                    res['message'] = 'Has pedido 0 del gasto {}, no es posible asignar nulo'
                else:
                    print('No encontramos el gasto deseado {} en el evento buscado: {}'.format(id_event, id_expense))
                    expense, statusCode = searchInExpense(id_expense)
                    if statusCode == 200:
                        available = expense[0]['available']
                        newAvailable = available - portionDesire
                        queryUpdateGastos = {'$push': {'allocation': {'id_event':id_event}}, '$set': {'available': newAvailable}}
                        queryUpdateAgenda = {'$push': {'expenses': {'id_expense':id_expense,'portion' : portionDesire}}}
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
    elif checkData(data, ['id_event', 'payments', 'food', 'beverages', 'furniture', 'others', 'margin', 'cost', 'price','salonPrice','utility'],
        {'id_event':str, 'payments':list, 'food':[int,float], 'beverages':[int,float], 'furniture':[int,float], 'others':[int,float], 'margin':[int,float], 
         'cost':[int,float], 'price':[int,float],'salonPrice':[int,float],'utility':[int,float]})[0]:
            if agendaTable.find_one({'id_event': data['id_event']}):
                id_event = data['id_event'] 
                del data['id_event'] 
                del data['payments']
                del data['price']
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

def fixData(result):
    result['beverages'] = result['margin']['beverages']
    result['food'] = result['margin']['food']
    result['furniture'] = result['margin']['furniture']
    result['salaries'] = result['margin']['salaries']
    result['others'] = result['margin']['others']
    result['utility'] = result['margin']['utility']
    result['egresses'] = result['margin']['cost']
    result['salonPrice'] = result['margin']['salonPrice']
    result['margin'] = result['margin']['margin']
    return result


def getMargenResultados(request):
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
        result = agendaTable.find_one({'id_event':data['id_event'], 'state':'completado'}, {'_id':0, 'expenses': 0})
        if result:
            payments = getPayments({'id_event':data['id_event']})
            dollarValue = ['cost', 'upfront', 'egresses', 'utility', 'food', 'beverages', 'salaries', 'others', 'salonPrice']
            inThousands = ['num_of_people', 'margin']
            headers = {
                'name':'nombre', 'type':'categoria', 'year':'año', 'day':'día', 'month':'mes', 
                'location':'ubicacion', 'num_of_people':'invitados', 'cost':'precio', 'upfront':'adelanto', 
                'state':'estado','margin': 'margen', 'egresses':'coste', 'utility':'utilidad', 'food':'comida',
                'beverages':'bebidas', 'salaries':'salarios',
                'others': 'otros', 'salonPrice': 'costo_salon'
            }
            result = fixData(result)
            index = 1
            print(payments)
            for payment in payments:
                headers['payment{}'.format(index)] = 'pago_{}'.format(index)
                result['payment{}'.format(index)] = payment
                dollarValue.append('payment{}'.format(index))
                index +=1 
            df = pd.DataFrame([result])
            return returnExcel(df, headers, 'margen', 'detalles', dollarValue, inThousands)
        else:
            res['message'] = 'Evento no tiene margen de resultados concluido'
            statusCode = 404
    else:
        res['message'] = 'No se envio el id del evento'
        statusCode = 400
    print(data)
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