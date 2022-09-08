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
    if (not(len(sys.argv) == 9)):
        print('[-] Incorrect number of arguments')
        print('python run.py [username] [password] [host] [port] [dbname]')
        sys.exit()
    else:
        username = sys.argv[1]
        password = sys.argv[2]
        host = sys.argv[3]
        port = sys.argv[4]
        dbname = sys.argv[5]
        # username1 = sys.argv[6]
        # password1 = sys.argv[7]
        host1 = sys.argv[6]
        port1 = sys.argv[7]
        dbname1 = sys.argv[8]
        mongoUri = 'mongodb://%s:%s@%s:%s/?authMechanism=DEFAULT&authSource=%s' % (username, password, host, port, dbname)
        conn = MongoClient(mongoUri)
        collections = ['users_user', 'users_visitor', 'users_timezone', 'django_session']
        try:
            dump(collections, conn, 'djongo', 'backups')
            print('[*] Successfully performed backup')
        except Exception as e:
            print('Error: '+ str(e) )
            print('EXIT')
        conn1 = MongoClient('mongodb://%s:%s' % (host1, port1))
        try:
            restore('backups', conn1, dbname1)
            print('[*] Successfully performed backup')
        except Exception as e:
            print('Error: '+ str(e) )
            print('EXIT')
