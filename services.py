from datetime import datetime, timedelta, timezone
import mysql.connector

__all__ = ['Service', 'nocommit']

class Database:
    # Reconnection timeout
    timeout = timedelta(seconds=300)

    def __init__(self):
        self.last = None

    def execute(self, query, params):
        now = datetime.now(tz=timezone.utc)
        if not self.last or (now - self.last) > self.timeout:
            import database
            self.db = mysql.connector.connect(
                host = database.dbhost,
                user = database.dbuser,
                password = database.dbpw,
                database = database.dbname,
                use_unicode = True,
                autocommit = True,
            )
            del database
            self.cursor = self.db.cursor(prepared=True)
            self.last = now

        try:
            return self.cursor.execute(query, params)
        except:
            # Retry once
            self.db.reconnect()
        return self.cursor.execute(query, params)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

dbcursor = Database()

class Service:
    def __init__(self, service_name):
        self.name = service_name

    def __getitem__(self, client_name):
        return Client(self, client_name)

    def __delitem__(self, client_name):
        if type(client_name) == Client:
            client_name = client_name.name
        dbcursor.execute(
            'DELETE FROM `services` WHERE `service` = %s AND `client` = %s',
            (self.name, client_name))

    def __iter__(self):
        dbcursor.execute(
            'SELECT DISTINCT `client` FROM `services` WHERE `service` = %s',
            (self.name,))
        return [Client(self, row[0]) for row in dbcursor.fetchall()].__iter__()

class Client:
    def __init__(self, service, client_name):
        self.service = service
        self.name = client_name

    def __getitem__(self, key):
        dbcursor.execute(
            'SELECT `value` FROM `services` WHERE `service` = %s AND `client` = %s AND `key` = %s',
            (self.service.name, self.name, key))
        result = dbcursor.fetchone()
        if result == None:
            return None
        return result[0]

    def __setitem__(self, key, value):
        if not isinstance(value, bytearray):
            value = str(value)
        dbcursor.execute(
            'INSERT INTO `services` (`service`, `client`, `key`, `value`) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE `value` = VALUE(`value`)',
            (self.service.name, self.name, key, value))

    def __delitem__(self, key):
        dbcursor.execute(
            'DELETE FROM `services` WHERE `service` = %s AND `client` = %s AND `key` = %s',
            (self.service.name, self.name, key))

    def __iter__(self):
        dbcursor.execute(
            'SELECT `key` FROM `services` WHERE `service` = %s AND `client` = %s',
            (self.service.name, self.name))
        return [row[0] for row in dbcursor.fetchall()].__iter__()

def nocommit():
    # Only for testing, no need to commit
    dbcursor.db.autocommit = False

def main():
    nocommit()

    service = Service('test')
    client1 = service['client1']
    client2 = service['client2']

    client1['key1'] = b'value1'
    value = client1['key1']
    if value != b'value1':
        raise Exception(f'wrong value: {value}')

    client2['key2'] = b'value2'
    value = client2['key2']
    if value != b'value2':
        raise Exception(f'wrong value: {value}')

    print(f'Clients: {[client for client in service]}')
    print(f'Client client1 Keys: {[key for key in client1]}')
    print(f'Client client2 Keys: {[key for key in client2]}')

    del client1['key1']
    value = client1['key1']
    if value != None:
        raise Exception(f'wrong value: {value}')

    for c in service:
        del service[c]

    print(f'Clients deleted: {[client for client in service]}')

    print('all ok')
    return 0

if __name__ == '__main__':
    main()
