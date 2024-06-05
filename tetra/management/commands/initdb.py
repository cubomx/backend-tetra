# management/commands/initdb.py

from django.core.management.base import BaseCommand
from django.conf import settings
import pymongo
import json
import sys, os
sys.path.append('../')
from helpers.helpers import updateData

client =  pymongo.MongoClient(settings.DB['HOST'], settings.DB['PORT'], username=settings.DB['USER'], password=settings.DB['PASS'])
db = client[settings.DB['NAME']]
configTable = db['configuraciones']




class Command(BaseCommand):
    help = 'Initialize app options (locations, types of events, concepts, providers)'

    def handle(self, *args, **kwargs):
        def addOption(table, values, keyToSearch, messageToDisplay):
            query = { keyToSearch: { '$exists': True } }
            result = table.find_one(query)
            if result == None:
                resultInsert = table.insert_one({keyToSearch: []})
                if resultInsert.inserted_id:
                    self.stdout.write(self.style.SUCCESS('Ha sido inicializado exitosamente las opciones {}'.format(keyToSearch)))
                else:
                    self.stdout.write(self.style.ERROR('Hubo un error al querer insertar el nuevo {} opciones'.format(keyToSearch)))
            for option in values:
                # check duplicates
                if table.find_one({keyToSearch:option}) != None:
                    self.stdout.write(self.style.WARNING('El {} {} ya esta disponible para seleccionar'.format(messageToDisplay, option)))
                else:
                    update_query = {'$addToSet': {keyToSearch: option}}
                    result = updateData(table, query, update_query)
                    if result['result'] > 0:
                        self.stdout.write(self.style.SUCCESS('Fue agregado con exito el nuevo {} {}'.format(messageToDisplay, option)))
                    else:
                        self.stdout.write(self.style.ERROR('Hubo un error al querer insertar el nuevo {} {}'.format(messageToDisplay, option)))
        def load_json(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)

        # Define the path to your JSON files
        base_dir = os.path.dirname(os.path.abspath(__file__)) + '/data'
        places = load_json(os.path.join(base_dir, 'places.json'))
        types = load_json(os.path.join(base_dir, 'types.json'))
        in_concepts = load_json(os.path.join(base_dir, 'in_concepts.json'))
        out_concepts = load_json(os.path.join(base_dir, 'out_concepts.json'))
        gen_concepts = load_json(os.path.join(base_dir, 'gen_concepts.json'))
        providers = load_json(os.path.join(base_dir, 'providers.json'))
        gen_providers = load_json(os.path.join(base_dir, 'gen_providers.json'))

        addOption(configTable, places, 'locations', 'lugar')
        addOption(configTable, types, 'types', 'tipo de evento')
        addOption(configTable, in_concepts, 'in_concepts', 'concepto de ingreso')
        addOption(configTable, out_concepts, 'out_concepts', 'concepto de egreso')
        addOption(configTable, gen_concepts, 'gen_concepts', 'concepto de gasto general')
        addOption(configTable, providers, 'providers', 'proveedores')
        addOption(configTable, gen_providers, 'gen_providers', 'proveedores generales')
