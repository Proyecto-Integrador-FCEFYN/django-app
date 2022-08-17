from django.conf import settings
import socket


def test_connection_to_db(database_name):
    try:
        db_definition = getattr(settings, 'DATABASES')[database_name]
        s = socket.create_connection((db_definition['my_host'], db_definition['my_port']), 5)
        s.close()
        return True
    except:
        return False


class dbRouter(object):
    """A router that defaults reads to the follower but provides a failover back to the default"""

    def db_for_read(self, model, **hints):
        if test_connection_to_db('default'):
            return 'default'
        return 'backup'

    def db_for_write(self, model, **hints):
        if test_connection_to_db('default'):
            return 'default'
        return 'backup'

    def allow_syncdb(self, db, model):
        "Make sure only the default db allows syncdb"
        return db == 'default'
