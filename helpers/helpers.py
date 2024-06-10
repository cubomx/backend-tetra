import secrets
from datetime import datetime
from tempfile import NamedTemporaryFile
from django.utils.encoding import smart_str
from django.http import HttpResponse
import pandas as pd
import openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO

meses_del_año = ["0", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


path = "salida.xlsx"

#Funcion que extrae los valores del archivo de excel que se mande, se debe mandar el workbook, no el path
def extrar_data(wb):
    sheet = wb.active
    encabezado_bool = True
    encabezados = []
    pagos_indices = []
    eventos=[]
    for row in sheet.iter_rows():
        evento_info = []
        pagos = []
        
        #La primer fila siempre serán los encabezados
        if encabezado_bool:
            for idx, cell in enumerate(row):
                if cell.value is not None:
                    if "pago" in cell.value.split("_"):
                        pagos.append(cell.value)
                        pagos_indices.append(idx)
                    else:
                        
                        encabezados.append(cell.value)
            encabezados.append(pagos)
            encabezado_bool = False
        
        #El resto de las filas son eventos
        else:
            for idx, cell in enumerate(row):
                if idx in pagos_indices:
                    pagos.append(cell.value)
                else:
                    evento_info.append(cell.value)
            evento_info.append(pagos)
            #Eliminamos el primer valor de la lista, ya que es el indice del evento y es un dato irrevelante.
            #evento_info.pop(0)

            #Agregamos la informacion de cada evento a una lista de eventos
            eventos.append(evento_info)
    #retornamos una lista de los encabezados, y una lista de eventos que contiene una lista de cada evento con su informción.
    return encabezados, eventos



# Función para crear un nuevo archivo de Excel y agregar los eventos
def dar_formato(encabezados, eventos):
    wb_nuevo = Workbook()
    # Eliminar la hoja de ejemplo creada por defecto
    wb_nuevo.remove(wb_nuevo.active)
    for i in range(len(eventos)):
        # Crear una nueva hoja para cada evento
        hoja = wb_nuevo.create_sheet(title=eventos[i][9])
        
        hoja["B3"].value = "Estado:"
        hoja["B3"].font = Font(bold=True)
        hoja["C3"].value = eventos[i][10]
        hoja["C3"].alignment = Alignment(horizontal="center")  # Alineación al centro
        if eventos[i][10] == "completado":
            hoja["D3"].fill = PatternFill(start_color="05A625", end_color="05A625", fill_type="solid")  # Relleno amarillo sólido
        elif eventos[i][10] == "cancelado":
            hoja["D3"].fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")  # Relleno amarillo sólido

        hoja["B5"].value = "Cliente:"
        hoja["B5"].font = Font(bold=True)
        hoja["C5"].value = eventos[i][0]
        hoja["C5"].alignment = Alignment(horizontal="center")  # Alineación al centro
        

        hoja["B7"].value = "Evento:"
        hoja["B7"].font = Font(bold=True)
        hoja["C7"].value = eventos[i][1]
        hoja["C7"].alignment = Alignment(horizontal="center")  # Alineación al centro

        hoja["B9"].value = "Fecha:"
        hoja["B9"].font = Font(bold=True)
        print((eventos[i][9]))
        hoja["C9"].value = str(eventos[i][2])+"-"+meses_del_año[int(eventos[i][3])]+"-"+str(eventos[i][4])
        hoja["C9"].alignment = Alignment(horizontal="center")  # Alineación al centro
        
        hoja["B11"].value = "Ubicación:"
        hoja["B11"].font = Font(bold=True)
        hoja["C11"].value = eventos[i][5]
        hoja["C11"].alignment = Alignment(horizontal="center")  # Alineación al centro

        hoja["B13"].value = "No. Personas:"
        hoja["B13"].font = Font(bold=True)
        hoja["C13"].value = int(float(eventos[i][6]))
        hoja["C13"].alignment = Alignment(horizontal="center")  # Alineación al centro
        
        if eventos[i][10].lower() != "cancelado":

            # Asignar texto y formato a las celdas F3 y I3
            hoja["F3"].value = "SALIDAS:"
            hoja["F3"].font = Font(bold=True)
            hoja["F3"].alignment = Alignment(horizontal="center")  # Alineación al centro
            hoja["F3"].border = Border(bottom=Side(style='thick', color='FF0000'))  # Borde inferior rojo
            hoja["G3"].border = Border(bottom=Side(style='thick', color='FF0000'))  # Borde inferior rojo

            hoja["F5"].value = "Bebidas:"
            hoja["F5"].font = Font(bold=True)
            hoja["G5"].value = float(eventos[i][12][1:].replace(",", ""))
            hoja["G5"].number_format = '"$"#,##0.00'
            hoja["G5"].alignment = Alignment(horizontal="center")  # Alineación al centro

            hoja["F7"].value = "Comidas:"
            hoja["F7"].font = Font(bold=True)
            hoja["G7"].value = float(eventos[i][13][1:].replace(",", ""))
            hoja["G7"].number_format = '"$"#,##0.00'
            hoja["G7"].alignment = Alignment(horizontal="center")  # Alineación al centro

            hoja["F9"].value = "Mobiliario:"
            hoja["F9"].font = Font(bold=True)
            hoja["G9"].value = float(eventos[i][14][1:].replace(",", ""))
            hoja["G9"].number_format = '"$"#,##0.00'
            hoja["G9"].alignment = Alignment(horizontal="center")  # Alineación al centro

            hoja["F11"].value = "Salarios:"
            hoja["F11"].font = Font(bold=True)
            hoja["G11"].value = float(eventos[i][15][1:].replace(",", ""))
            hoja["G11"].number_format = '"$"#,##0.00'
            hoja["G11"].alignment = Alignment(horizontal="center")  # Alineación al centro

            hoja["F13"].value = "Otros:"
            hoja["F13"].font = Font(bold=True)
            hoja["G13"].value = float(eventos[i][16][1:].replace(",", ""))
            hoja["G13"].number_format = '"$"#,##0.00'
            hoja["G13"].alignment = Alignment(horizontal="center")  # Alineación al centro

            hoja["F15"].value = "Total gastos:"
            hoja["F15"].font = Font(bold=True)
            hoja["F15"].border = Border(top=Side(style='thick', color='FF0000'))  # Borde superior rojo
            hoja["G15"].value = "=G5+G7+G9+G11+G13"
            hoja["G15"].number_format = '"$"#,##0.00'
            hoja["G15"].alignment = Alignment(horizontal="center")  # Alineación al centro
            hoja["G15"].border = Border(top=Side(style='thick', color='FF0000'))  # Borde superior rojo


            hoja["I3"].value = "INGRESOS:"
            hoja["I3"].font = Font(bold=True)
            hoja["I3"].alignment = Alignment(horizontal="center")  # Alineación al centro
            hoja["I3"].border = Border(bottom=Side(style='thick', color='00FF00'))  # Borde inferior verde
            hoja["J3"].border = Border(bottom=Side(style='thick', color='00FF00'))  # Borde inferior verde

            hoja["I5"].value = "Anticipo:"
            hoja["I5"].font = Font(bold=True)
            hoja["J5"].value = float(eventos[i][8][1:].replace(",", ""))
            hoja["J5"].number_format = '"$"#,##0.00'
            hoja["J5"].alignment = Alignment(horizontal="center")  # Alineación al centro
            formula = "=J5"  # Empezar la fórmula con el valor del anticipo en J5

            ultima_fila =""
            for j in range(len(eventos[i])-1, len(eventos[i])):
                for k in range(len(eventos[i][j])):
                    if eventos[i][j][k] is not None:
                        hoja["I"+f"{7+(k*2)}"].value = f"Pago-{k+1}:"
                        hoja["I"+f"{7+(k*2)}"].font = Font(bold=True)
                        hoja["J"+f"{7+(k*2)}"].value = float(eventos[i][j][k][1:].replace(",", ""))
                        hoja["J"+f"{7+(k*2)}"].number_format = '"$"#,##0.00'
                        hoja["J"+f"{7+(k*2)}"].alignment = Alignment(horizontal="center")  # Alineación al centro
                        formula += f"+J{7+(k*2)}"
                        ultima_fila = f"{7+(k*2)+2}"
                          
            
            hoja["I"+ultima_fila].value = "Total ingresos:"
            hoja["I"+ultima_fila].font = Font(bold=True)
            hoja["I"+ultima_fila].border = Border(top=Side(style='thick', color='00FF00'))  # Borde superior verde
            hoja["J"+ultima_fila].value = formula  # Asignar la fórmula creada
            hoja["J"+ultima_fila].number_format = '"$"#,##0.00'
            hoja["J"+ultima_fila].alignment = Alignment(horizontal="center")  # Alineación al centro
            hoja["J"+ultima_fila].border = Border(top=Side(style='thick', color='00FF00'))  # Borde superior verde
            

            # Crear la sección "ESTADO DE RESULTADOS" comenzando en L3
            hoja["L3"].value = "ESTADO DE RESULTADOS:"
            hoja["L3"].font = Font(bold=True)
            hoja["L3"].border = Border(bottom=Side(style='thick', color='000000'))  # Borde inferior negro
            hoja["M3"].border = Border(bottom=Side(style='thick', color='000000'))  # Borde inferior negro

            hoja["L5"].value = "Total ingresos:"
            hoja["L5"].font = Font(bold=True)
            hoja["M5"].value = formula  # Asignar la fórmula creada
            hoja["M5"].number_format = '"$"#,##0.00'
            hoja["M5"].alignment = Alignment(horizontal="center")

            hoja["L7"].value = "Total gastos:"
            hoja["L7"].font = Font(bold=True)
            hoja["M7"].value = "=G5+G7+G9+G11+G13"
            hoja["M7"].number_format = '"$"#,##0.00'
            hoja["M7"].alignment = Alignment(horizontal="center")

            hoja["L9"].value = "Utilidad:"
            hoja["L9"].font = Font(bold=True)
            hoja["L9"].alignment = Alignment(horizontal="center")
            hoja["L9"].border = Border(top=Side(style='thick', color='000000'))  # Borde superior negro
            hoja["M9"].value = f"=M5-M7"  # Fórmula para calcular el total
            hoja["M9"].number_format = '"$"#,##0.00'
            hoja["M9"].alignment = Alignment(horizontal="center")
            hoja["M9"].border = Border(top=Side(style='thick', color='000000'))  # Borde superior negro
            
            hoja["L11"].value = "  utilidad:"
            hoja["L11"].font = Font(bold=True)
            hoja["L11"].alignment = Alignment(horizontal="center")
            hoja["M11"].value = f"=M9/M7"  # Fórmula para calcular el total
            hoja["M11"].number_format = '0.00%'
            hoja["M11"].alignment = Alignment(horizontal="center")
            

            # Crear la sección "COSTO DE SALON" comenzando en L13
            hoja["L14"].value = "COSTO DEL SALON:"
            hoja["L14"].font = Font(bold=True)
            hoja["L14"].border = Border(bottom=Side(style='thick', color='000000'))  # Borde inferior negro
            hoja["M14"].border = Border(bottom=Side(style='thick', color='000000'))  # Borde inferior negro
            
            hoja["L16"].value = "Costo del salón:"
            hoja["L16"].font = Font(bold=True)
            hoja["M16"].value = float(eventos[i][19][1:].replace(",", ""))
            hoja["M16"].number_format = '"$"#,##0.00'
            hoja["M16"].alignment = Alignment(horizontal="center")  # Alineación al centro

        #for i in range(len(eventos[i][:])):
    return wb_nuevo


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
    
def searchWithPagination(pipeline, projection, collection, errorMessage):
    res = collection.aggregate(pipeline, projection)
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
    #check if month and day less than 10
    month = '0' + str(data['month']) if data['month'] < 10 else str(data['month'])
    day = '0' + str(data['day']) if data['day'] < 10 else str(data['day'])
    date = str(data['year'])[2:] + month + day
    random_string = secrets.token_hex(bytes)  # Generate a random hex string of 16 bytes (32 characters)
    id_evento = random_string + str(date)
    
    return ''.join(id_evento)

# check if contains all the expected_keys and not others
def checkData(data, keys, types):
    for key in keys:
        if key not in data:
            return (False, "Falta llave {} en la informacion enviada".format(key))
        if isinstance(types[key], list):
            isGood = False
            for type_ in types[key]:
                if isinstance(data[key], type_):
                    isGood = True
            if not isGood:
                return (False, "Tipo de data incorrecto {} en llave {}".format(type(data[key]), type_))
        elif not isinstance(data[key], types[key]):
            print(type(data[key]),types[key] )
            return (False, "Tipo de data incorrecto {} en llave {}".format(type(data[key]), key))
    return (True, "Los datos se ven bien")


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

    response['message'] = "Se modifico satisfactoriamente {} registros".format(update_result["nModified"])
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

def generateTicketNumber(date):
    random_start = secrets.token_hex(1)  
    randon_end = secrets.token_hex(1)
    new_date = date.split('-')
    new_date[2] = new_date[2][:2]
    print(new_date)
    id_ticket = [random_start] + new_date  + [randon_end]
    return ''.join(id_ticket)

def generateIDTicket(date):
    random_end = secrets.token_hex(2)  
    id_ticket = date + random_end
    return ''.join(id_ticket)

def findAbono(query, collection):
    res = list(collection.find(query))
    status = 200
    if not res:
        status = 404
        res = {'message' : 'Pagos no encontrados'}
    return (res, status)

def returnExcel(df, filename):
    response = None
    # Create a BytesIO buffer
    buffer = BytesIO()
    
    # Write the DataFrame to the buffer as an Excel file
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resumen Cliente')
    
    # Move the cursor of the buffer to the beginning
    buffer.seek(0)

    '''wb = load_workbook(buffer)
    encabezados, eventos = extrar_data(wb)
    wb_nuevo = dar_formato(encabezados, eventos)

    new_buffer = BytesIO()
    wb_nuevo.save(new_buffer)
    new_buffer.seek(0)
    '''
    # Create the HttpResponse with the appropriate content_type and headers
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="salida.xlsx"'
    

    return response