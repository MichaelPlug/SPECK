import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
import json
import requests 

"""
SPECK: Secrecy and Privacy Enhancer for Ciphered Knowledge
"""
class SPECK:
    def __init__(
            self,
            host = "172.18.0.3",
            port = 5432,
            database = "cake-db",
            user = "root",
            password = "root",
            API_URL = "http://0.0.0.0:8888/",
            DATA_OWNER_HANDSHAKE = False,
            handshaked_addresses = [],
            ) -> None:
        
        self.API_URL = API_URL
        self.DATA_OWNER_HANDSHAKE = DATA_OWNER_HANDSHAKE
        self.handshaked_addresses = handshaked_addresses

        # Database connection parameters
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password


    """
    Print the SPECK settings and the database connection parameters
    """
    def show_speck_info(self):
        print("SPECK info:")
        print("API url: \t", self.API_URL)
        print("Database connection parameters:")
        print("\tHost: \t", self.host)
        print("\tPort: \t", self.port)
        print("\tDatabase: \t", self.database)
        print("\tUser: \t", self.user)
        print("\tPassword: \t", self.password)
        print("Handshake enabled: \t", self.DATA_OWNER_HANDSHAKE)
        if self.DATA_OWNER_HANDSHAKE:
            print("\tAddresses that have already done the handshake: \t", self.handshaked_addresses)


    def __check_api_connection__(self):
        try:
            response = requests.get(self.API_URL)
            if response.status_code != 200:
                raise Exception("API does not respond correctly")
        except:
            raise Exception("API not reachable")\

    """
    Ceate a connection to the database

    isolation_level_autocommit: if True, the connection is set to autocommit mode
    """
    def __create_connnection__(self, isolation_level_autocommit = True):
        try:
            conn = psycopg2.connect(
                host = self.host,
                port = self.port,
                database = self.database,
                user = self.user,
                password = self.password
            )
            if isolation_level_autocommit:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            curs = conn.cursor()
        except:
            raise Exception("Unable to connect to the database")
        return conn, curs
    
    """
    Process an update event
    
    curs: cursor to the database
    conn: connection to the database
    query: query to execute
    close: if True, close the cursor and the connection at the end
    """
    def __execute_and_commit__(curs, conn, query, close=False):
        if conn.closed:
            raise Exception("Connection is closed")
        curs.execute(query)
        conn.commit()
        if close:
            curs.close()
            conn.close()

    """
    Send a message to the API

    data: data to send as attachment
    endpoint: endpoint to send the data to
    """
    def __send_to_api__(self, data, endpoint) -> bool:
        response = requests.post(self.API_URL + endpoint, json=data)
        print(response)

        if response.status_code != 200:
            print("Something went wrong with the API")
            return False
        print(response.text)
        return True

    """
    Read the result of a query

    res: result of a query, as a dictionary [string -> string]

    return: a tuple containing the blob, the message, the sender, the policy, the id, the list of entries, the entries and the process id
    """
    def __read_res__(res):
        blob = res["File"]
        message = bytearray.fromhex(blob[2:]).decode()
        sender = res["From"]
        policy = res["Policy"].strip('][').split(', ')
        id = res["ID"]
        list_of_entries = res["Entries"].split('], [')
        entries = [i.strip('][').split(', ') for i in list_of_entries]

        process_id = res["Process_id"]

        return blob, message, sender, policy, id, list_of_entries, entries, process_id
    
    def __build_data__(res, verbose = False) -> dict:
        _, message, sender, policy, id, _, entries, process_id = SPECK.__read_res__(res)

        data = {
            "message": message,
            "entries": entries,
            "sender": sender,
            "policy": policy,
            "process_id": process_id,
            "id": id
        }

        if verbose:
            print("Data: ", data)
        return data


    """
    Execute SPECK
    """
    def execute(self, check_already_read = True, time_to_sleep = 0.1):
        self.__check_api_connection__()
        print("Starting SPECK...")
        # Connect to the database
        conn, curs = self.__create_connnection__()

        # Enable LISTEN/NOTIFY for the trigger events
        curs.execute("LISTEN update_a_row_notification;")
        curs.execute("LISTEN update_notification;")

        if check_already_read:
            self.__execute_and_commit__(curs, conn, 'UPDATE public."CAKE-1" SET "Status"='+"'Ready'" +'WHERE "Status"='+"'Ready';")
        print("Waiting for trigger events...")

        while True:
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                if notify.channel == "update_notification":
                    self.__process_insert_event__(notify.payload)
                elif notify.channel == "update_a_row_notification":
                    self.__process_update_event__(notify.payload)
            time.sleep(time_to_sleep)
        # NOTE: This is not reachable
        curs.close()
        conn.close()
    
    """
    Execute SPECK in static mode
    """
    def static_execution(self): 
        self.__check_api_connection__()
        print("Starting SPECK...")
        # Connect to the database
        conn, curs = self.__create_connnection__()

        res = self.get_ready_rows(curs, conn).fetchall()

        for row in res:
            self.__process_insert_event__(row)

        curs.close()
        conn.close()
        print("SPECK terminated")
        return
        
    """
    Process an insert event
    """
    def __process_insert_event__(self, payload):
        #print("INSERT EVENT")
        print("Received trigger event:\n", payload)
        res = json.loads(payload)

        if res["Status"] != "Ready":
            print("Something went wrong. Initial status is not 'Ready'")
            return

        #blob, message, sender, policy, id, list_of_entries, entries, process_id = self.__read_res__(res)

        _, message, sender, policy, id, _, entries, process_id = self.__read_res__(res)

        data = {
            "message": message,
            "entries": entries,
            "sender": sender,
            "policy": policy,
            "process_id": process_id,
            "id": id
        }

        print("Data: ", data)

        if self.DATA_OWNER_HANDSHAKE:
            #if not self.handshaked_addresses[sender]:
            if sender not in self.handshaked_addresses:
                if not self.__send_to_api__(data, "dataOwner/handshake"):
                    return
                #self.handshaked_addresses[sender] = True
                self.handshaked_addresses.append(sender)

        conn, curs = self.__create_connnection__()
        self.__create_connnection__(curs, conn, 'UPDATE public."CAKE-1" SET "Status" = ' + "'Submitted'" + ' WHERE "ID" ='  + str(res["ID"]), close=True)
        '''
        curs.execute('UPDATE public."CAKE-1" SET "Status" = ' + "'Submitted'" + ' WHERE "ID" ='  + str(res["ID"]))
        conn.commit()

        curs.close()
        conn.close()
        '''
        if not self.__send_to_api__(data, "dataOwner/cipher"):
            return 

        conn, curs = self.__create_connnection__()
        self.__create_connnection__(curs, conn, 'UPDATE public."CAKE-1" SET "Status" = ' + "'Ciphered'" + ' WHERE "ID" ='  + str(res["ID"]), close=True)
        '''
        curs.execute('UPDATE public."CAKE-1" SET "Status" = ' + "'Ciphered'" + ' WHERE "ID" ='  + str(res["ID"]))
        conn.commit()
        curs.close()
        '''
        print("Updated the database to Ciphered")

    """
    Process an update event
    """
    def __process_update_event__(self, payload):
        #print("UPDATE EVENT")
        #print("Received trigger event:\n", payload)
        res = json.loads(payload)

        if res["Status"] == "Ready":
            self.process_insert_event(payload)
            return
        return
    
    def append_handshaked_address(self, address):
        self.handshaked_addresses.append(address)

    def __make_query_get_fetch__(self, curs, conn, query):
        curs.execute(query)
        res = curs.fetchall()
        curs.close()
        conn.close()
        return res

    def get_db_content(self):
        conn, curs = self.__create_connnection__()
        res = self.__make_query_get_fetch__(curs, conn, 'SELECT * FROM public."CAKE-1"')
        return res.fetchall()
    
    def get_ready_rows(self):
        conn, curs = self.__create_connnection__()
        res = self.__make_query_get_fetch__(curs, conn, 'SELECT * FROM public."CAKE-1" WHERE "Status"='+"'Ready'")
        return res.fetchall()
    
    def get_ciphered_rows(self):
        conn, curs = self.__create_connnection__()
        res = self.__make_query_get_fetch__(curs, conn, 'SELECT * FROM public."CAKE-1" WHERE "Status"='+"'Ciphered'")
        return res.fetchall()

    def get_submitted_rows(self):
        conn, curs = self.__create_connnection__()
        res = self.__make_query_get_fetch__(curs, conn, 'SELECT * FROM public."CAKE-1" WHERE "Status"='+"'Submitted'")
        return res.fetchall()
    
# Start listening for trigger events
if __name__ == "__main__":
    speck = SPECK()
    speck.show_speck_info()
    print(speck.get_db_content())
    #speck.execute()


