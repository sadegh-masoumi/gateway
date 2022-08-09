"""
connect to db and table transaction
# CREATE TABLE transaction (pk serial PRIMARY KEY,type VARCHAR ( 50 ) ,content VARCHAR ( 50 ),);
"""
from database import Crud


table = Crud(
    user='postgres',
    password='123456789',
    host='127.0.0.1',
    port='5432',
    dbname='postgres',
    table='transaction',
    primarykey='pk'
)
table.connect()
table.select_all()
