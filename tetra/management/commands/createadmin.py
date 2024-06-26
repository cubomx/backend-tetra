# management/commands/createadmin.py

from django.core.management.base import BaseCommand
from django.conf import settings
import pymongo
import sys
sys.path.append('../')
from helpers.admin import hashPassword

client = pymongo.MongoClient(settings.CONNECTION_STRING)
#client =  pymongo.MongoClient(settings.DB['HOST'], settings.DB['PORT'], username=settings.DB['USER'], password=settings.DB['PASS'])
db = client[settings.DB['NAME']]
usuariosTable = db['usuarios']

class Command(BaseCommand):
    help = 'Create a master administrator'

    def handle(self, *args, **kwargs):
        if len(list(usuariosTable.find({'role':'admin'}))) == 0:
            email = input('Enter email for master administrator: ')
            password = input('Enter password for master administrator: ')
            hashedPass = hashPassword(password).decode('utf-8')
            
            role = 'admin'
            res = usuariosTable.insert_one({'email': email, 'name':'Admin', 'password':hashedPass, 'role': role, 'isMaster':True})
            if res.inserted_id:
                self.stdout.write(self.style.SUCCESS('El administrador ha sido creado con exito'))
            else:
                self.stdout.write(self.style.ERROR('Ha habido un error al intentar crear el usuario'))

        else:
            self.stdout.write(self.style.WARNING('Ya existe un administraor, saltando esta parte'))
