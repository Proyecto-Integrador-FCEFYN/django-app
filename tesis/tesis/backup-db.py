import bson, sys, os, os.path
from pymongo import MongoClient
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

def dump(collections, conn, db_name, path):
    """
    MongoDB Dump
    :param collections: Lista de las colecciones a ser descargadas
    :param conn: Conexión MongoDB a la cual hacer backup.
    :param db_name: Nombre de base de datos a hacer el backup.
    :param path: Path relativo donde guardar el backup.
    :return: None
    
    >>> DB_BACKUP_DIR = '/path/backups/'
    >>> conn = MongoClient("mongodb://admin:admin@127.0.0.1:27017", authSource="admin")
    >>> db_name = 'my_db'
    >>> collections = ['collection_name', 'collection_name1', 'collection_name2']
    >>> dump(collections, conn, db_name, DB_BACKUP_DIR)
    """
    if not os.path.exists(path):
        os.makedirs(path)
    db = conn[db_name]
    if collections == 'all':
        collections = db.collection_names()
    print('Haciendo backup de las siguientes colecciones:')
    print(collections)
    for coll in collections:
        with open(os.path.join(path, f'{coll}.bson'), 'wb+') as f:
            for doc in db[coll].find():
                f.write(bson.BSON.encode(doc))


def restore(path, conn, db_name):
    """
    MongoDB Restore
    :param path: Path relativo de donde hacer backup.
    :param conn: Conexión MongoDB a donde hacer el restore.
    :param db_name: Nombre de base de datos a donde restaurar.
    :return:
    
    >>> DB_BACKUP_DIR = '/path/backups/'
    >>> conn = MongoClient("mongodb://admin:admin@127.0.0.1:27017", authSource="admin")
    >>> db_name = 'my_db'
    >>> restore(DB_BACKUP_DIR, conn, db_name)
    
    """
    
    db = conn[db_name]
    for coll in os.listdir(path):
        if coll.endswith('.bson'):
            with open(os.path.join(path, coll), 'rb+') as f:
                for document in bson.decode_all(f.read()):
                    filter_values = {'_id' : document.get('_id')}
                    newvalues = { "$set": document }
                    db[coll.split('.')[0]].update_one(filter_values, newvalues, True)

if __name__ == '__main__':
    if (not(len(sys.argv) == 11 or 12)):
        print('Número incorrecto de parámetros.')
        print('Los cinco primeros parámetros refieren a la BD de origen' + \
        ' y los cinco siguientes refieren a la de destino. Ej:' + '\n' +
        ' python3 backup-db.py [username1] [password1] [host1] [port1] [dbname1]  ' +\
        '[username2] [password2] [host2] [port2] [dbname2]' + '\n' +
        'En caso de que la base no tenga usuario y contraseña configurados, escribir un guión medio (-) ' +\
        'en su lugar.')
        print("Especifique '--all' si quiere hacer backup de todas las colleciones de la base de origen.")
        sys.exit()
    else:
        all_collections = False
        if len(sys.argv) == 12:
            if sys.argv[11] in '--all':
                all_collections = True
            else:
                print('Parámetros incorrectos.')
                print("Especifique '--all' si quiere hacer backup de todas las colleciones de la base de origen.")
                sys.exit()

        # Parseo de parámetros de base de datos de origen
        username_origen = sys.argv[1]
        password_origen = sys.argv[2]
        host_origen = sys.argv[3]
        port_origen = sys.argv[4]
        dbname_origen = sys.argv[5]

        # Parseo de parámetros de base de datos de destino
        username_dest = sys.argv[6]
        password_dest = sys.argv[7]
        host_dest = sys.argv[8]
        port_dest = sys.argv[9]
        dbname_dest = sys.argv[10]

        # Creación de URI de origen.
        # En caso de recibir un '-', el URI no va a tener usuario y contraseña.
        if ((username_origen in '-') or (password_origen in '-')):
            mongoUri_source = 'mongodb://%s:%s' % (host_origen, port_origen)
        else:
            mongoUri_source = 'mongodb://%s:%s@%s:%s/?authMechanism=DEFAULT&authSource=%s' % (
                username_origen, password_origen, host_origen, port_origen, dbname_origen)

        # Creación de URI de destino
        # En caso de recibir un '-', el URI no va a tener usuario y contraseña.
        if ((username_dest in '-') or (password_dest in '-')):
            mongoUri_dest = 'mongodb://%s:%s' % (host_dest, port_dest)
        else:
            mongoUri_dest = 'mongodb://%s:%s@%s:%s/?authMechanism=DEFAULT&authSource=%s' % (
                username_origen, password_origen, host_origen, port_origen, dbname_origen)

        conn = MongoClient(mongoUri_source)

        if all_collections:
            backup_path = 'backup_all'
            collections = 'all'
        else:
            backup_path = 'backups'
            collections = ['users_user', 'users_visitor', 'users_timezone', 'django_session']
        try:
            dump(collections, conn, dbname_origen, backup_path)
            print('Backup realizado con éxito.')
        except Exception as e:
            print('Error: '+ str(e) )
            print('EXIT')
        conn1 = MongoClient(mongoUri_dest)
        try:
            restore(backup_path, conn1, dbname_dest)
            print('Restore realizado con éxito.')
        except Exception as e:
            print('Error: '+ str(e) )
            print('EXIT')

