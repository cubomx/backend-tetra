import secrets
from datetime import datetime
from tempfile import NamedTemporaryFile
from django.utils.encoding import smart_str
from django.http import HttpResponse
import pandas as pd

def search(query, collection):
    return list(collection.find(query))

def searchWithProjection(query, projection, collection, errorMessage):
    res = list(collection.find (query, projection))
    if not res:
        status = 404
        res = [{'message' : errorMessage}]
        return (res, status)
    else:
        return (res, 200) 
    
def deleteExtraQueries(data, expected_keys):
        # Get the keys of the JSON object
    data_keys = data.keys()
    
    # Check if all keys are in the expected keys list
    for key in data_keys:
        if key not in expected_keys:
            del data[key]
    return data

def getIDEvento(data, bytes):
    # Generate a random string
    date = str(data['year']) + str(data['month']) + str(data['day'])
    random_string = secrets.token_hex(bytes)  # Generate a random hex string of 16 bytes (32 characters)
    id_evento = random_string + str(date)
    
    return ''.join(id_evento)

# check if contains all the expected_keys and not others
def checkData(data, keys, types):
    for key in keys:
        if key not in data:
            return (False, "Missing key {} in data sent".format(key))
        elif not isinstance(data[key], types[key]):
            print(type(data[key]),types[key] )
            return (False, "Wrong type {} in key {}".format(type(data[key]), key))
    return (True, "Data seems good")


# check if contains keys between a range
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
    response = {}

    update_result = res.raw_result

    response['message'] = "Se modifico satisfactoriamente {} rows".format(update_result["nModified"])
    response['result'] = update_result["nModified"]

    return response

def checkForChangeOfID(data, collection):
    id_evento = data['id_evento']
    old_id = id_evento
    
    res = collection.find_one({'id_evento' : id_evento})
    if res['location'] != data['location'] or res['date'] != data['date']:
        return (getIDEvento(data), old_id)
    return (id_evento, id_evento)

def getDate():
    present_date = datetime.now().date()
    present_date_str = present_date.strftime("%d-%m-%Y")
    return present_date_str

def generateTicketNumber(bytes, date):
    random_start = secrets.token_hex(bytes)  
    randon_end = secrets.token_hex(bytes)
    id_ticket = [random_start] + date.split('-') + [randon_end]
    return ''.join(id_ticket)

def generateIDTicket(bytes, date):
    random_end = secrets.token_hex(bytes)  
    id_ticket = date + random_end
    return ''.join(id_ticket)

def findAbono(query, collection):
    res = list(collection.find(query))
    status = 200
    if not res:
        status = 404
        res = [{'message' : 'ERROR. Payment not found'}]
    return (res, status)

def returnExcel(df, headers, filename, sheet_name):
    response = None
    
    # add format
    df['cost'] = '$' + (df['cost'].map('{:,.2f}'.format)).astype(str)
    df['upfront'] = '$' + (df['upfront'].map('{:,.2f}'.format)).astype(str)

    df.rename(columns=headers, inplace = True)
    # Create a temporary file to save the Excel data
    with NamedTemporaryFile(delete=True, suffix=".csv") as tmp:
        response = HttpResponse(content_type='application/xlsx')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        with pd.ExcelWriter(response) as writer:
            df.to_excel(writer, sheet_name=sheet_name)

    return response