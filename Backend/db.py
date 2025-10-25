import pymysql
from pymysql.cursors import DictCursor

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="R@g!n!22",
        database="mmse_db",
        cursorclass=DictCursor   # ← important
    )
