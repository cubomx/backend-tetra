import sys
import json
sys.path.append('../')
from helpers.helpers import checkData, updateData


def addToOptions(table, request, keys, types,  keyToSearch, messageToDisplay):
    data = json.loads(request.body.decode('utf-8'))
    res = {}
    isDataCorrect, message = checkData(data, keys, types)
    statusCode = 200
    if isDataCorrect:
        query = { keyToSearch: { '$exists': True } }
        result = table.find_one(query)
        if result != None:
            # check duplicates
            if table.find_one({keyToSearch:data[keys[0]]}) != None:
                statusCode = 406
                res['message'] = 'El {} {} ya esta disponible para seleccionar'.format(messageToDisplay, data[keys[0]])
            else:
                update_query = {'$addToSet': {keyToSearch: data[keys[0]]}}
                result = updateData(table, query, update_query)
                if result['result'] > 0:
                    res['message'] = 'Fue agregado con exito el nuevo {} {}'.format(messageToDisplay, data[keys[0]])
                else:
                    statusCode = 500
                    res['message'] = 'Hubo un error al querer insertar el nuevo {} {}'.format(messageToDisplay, data[keys[0]])
        else:
            resultInsert = table.insert_one({keyToSearch: [data[keys[0]]]})
            if resultInsert.inserted_id:
                res['message'] = 'Fue agregado con exito el nuevo {} {}'.format(messageToDisplay, data[keys[0]])
            else:
                statusCode = 500
                res['message'] = 'Hubo un error al querer insertar el nuevo {} {}'.format(messageToDisplay, data[keys[0]])
    else:
        statusCode = 400
        res['message'] = message

    return (res, statusCode)

def getOptions(table, keyToSearch, messageToDisplay):
    res = {}

    statusCode = 200
    query = { keyToSearch: { '$exists': True } }
    result = table.find_one(query)
    if result != None:
        print(result)
        res[keyToSearch] = result[keyToSearch]
    else:
        res['message'] = 'No se encontro ningun {}, dile al administrador que agregue'.format(messageToDisplay)
        statusCode = 404
    return (res, statusCode)

def delOptions(table, request, keys, types, keyToSearch, messageToDisplay):
    data = json.loads(request.body.decode('utf-8'))
    res = {}
    print(data)
    isDataCorrect, message = checkData(data, keys, types)
    statusCode = 200
    if isDataCorrect:
        query = { keyToSearch: { '$exists': True } }
        delUpdate = {'$pull': {keyToSearch: data[keys[0]]}}
        result = updateData(table, query, delUpdate)
        if result['result'] > 0:
            res['message'] = 'Se elimino el {} {} satisfactoriamente'.format(messageToDisplay, data[keys[0]])
        else:
            res['message'] = 'Hubo un error al eliminar el {} {}'.format(messageToDisplay, data[keys[0]])
            statusCode = 500
    else:
        statusCode = 400
        res['message'] = message
    return (res, statusCode)