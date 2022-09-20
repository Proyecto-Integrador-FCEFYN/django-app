import bson, sys, os, os.path
from pymongo import MongoClient

def dump(collections, conn, db_name, path):
    """
    MongoDB Dump
    :param collections: Database collections name
    :param conn: MongoDB client connection
    :param db_name: Database name
    :param path:
    :return:
    
    >>> DB_BACKUP_DIR = '/path/backups/'
    >>> conn = MongoClient("mongodb://admin:admin@127.0.0.1:27017", authSource="admin")
    >>> db_name = 'my_db'
    >>> collections = ['collection_name', 'collection_name1', 'collection_name2']
    >>> dump(collections, conn, db_name, DB_BACKUP_DIR)
    """

    db = conn[db_name]
    for coll in collections:
        with open(os.path.join(path, f'{coll}.bson'), 'wb+') as f:
            for doc in db[coll].find():
                f.write(bson.BSON.encode(doc))


def restore(path, conn, db_name):
    """
    MongoDB Restore
    :param path: Database dumped path
    :param conn: MongoDB client connection
    :param db_name: Database name
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
                db[coll.split('.')[0]].insert_many(bson.decode_all(f.read()))

if __name__ == '__main__':
    if (not(len(sys.argv) == 11)):
        print('[-] Incorrect number of arguments (%s)', len(sys.argv))
        print('Los cinco primeros parámetros refieren a la BD de origen' + \
        ' y los cinco siguientes refieren a la de origen. Ej:' + '\n' +
        ' python3 backup-db.py [username1] [password1] [host1] [port1] [dbname1]  ' +\
        '[username2] [password2] [host2] [port2] [dbname2]')
        sys.exit()
    else:
        username_origen = sys.argv[1]
        password_origen = sys.argv[2]
        host_origen = sys.argv[3]
        port_origen = sys.argv[4]
        dbname_origen = sys.argv[5]
        username_dest = sys.argv[6]
        password_dest = sys.argv[7]
        host_dest = sys.argv[8]
        port_dest = sys.argv[9]
        dbname_dest = sys.argv[10]
        mongoUri_source = 'mongodb://%s:%s@%s:%s/?authMechanism=DEFAULT&authSource=%s' % (
            username_origen, password_origen, host_origen, port_origen, dbname_origen)
        mongoUri_dest = 'mongodb://%s:%s@%s:%s/?authMechanism=DEFAULT&authSource=%s' % (
            username_origen, password_origen, host_origen, port_origen, dbname_origen)
        conn = MongoClient(mongoUri_source)
        collections = ['users_user', 'users_visitor', 'users_timezone', 'django_session']
        try:
            dump(collections, conn, dbname_origen, 'backups')
            # run_backup(mongoUri, dbname)
            print('[*] Successfully performed backup')
        except Exception as e:
            print('[-] An unexpected error has occurred')
            print('[-] '+ str(e) )
            print('[-] EXIT')
        conn1 = MongoClient(mongoUri_dest)
        try:
            restore('backups', conn1, dbname_dest)
            # run_backup(mongoUri, dbname)
            print('[*] Successfully performed backup')
        except Exception as e:
            print('[-] An unexpected error has occurred')
            print('[-] '+ str(e) )
            print('[-] EXIT')
