def checkAvailability(query, collection):
    return list(collection.find(query))

def getIDEvento(data):
    # Get Each Initial Char from the salon name
    id_evento = [word[0].upper() for word in data['location'].split()]
    # get evento date
    id_evento += ['_'] + data['date'].split('-')
    
    return ''.join(id_evento)

def checkData(data, keys):
    for key in keys:
        if key not in data:
            return (False, "Missing key {} in data sent".format(key))
    return (True, "Data seems good")

def check_keys(data, expected_keys):
    # Get the keys of the JSON object
    data_keys = data.keys()
    
    # Check if all keys are in the expected keys list
    for key in data_keys:
        if key not in expected_keys:
            return False
    return True

def updateData(collection, query, updateQuery):
    res = collection.update_one(query, updateQuery)

    update_result = res.raw_result
    

    response = {"Matched" : "{} rows".format(update_result["n"])}
    response["Modified"] = "{} rows".format(update_result["nModified"])

    return response

def checkForChangeOfID(data, collection):
    id_evento = data['id_evento']
    old_id = id_evento
    
    res = collection.find_one({'id_evento' : id_evento})
    if res['location'] != data['location'] or res['date'] != data['date']:
        return (getIDEvento(data), old_id)
    return (id_evento, id_evento)