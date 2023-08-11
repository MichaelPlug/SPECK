import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
import json
import requests

# TODO: Manage possible errors
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

        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    def __create_connnection__(self, isolation_level_autocommit = True):
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

        return conn, curs

    def listen_for_trigger_events(self, check_already_read = True, time_to_sleep = 0.1):
        # Connect to the database
        conn, curs = self.__create_connnection__()

        # Enable LISTEN/NOTIFY for the trigger events
        curs.execute("LISTEN update_a_row_notification;")
        curs.execute("LISTEN update_notification;")

        if check_already_read:
            curs.execute('UPDATE public."CAKE-1" SET "Status"='+"'Ready'" +'WHERE "Status"='+"'Ready';")
            conn.commit()
        print("Waiting for trigger events...")
        # TODO: Check if some Ready rows are already in the database
        while True:
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                if notify.channel == "update_notification":
                    self.process_insert_event(notify.payload)
                elif notify.channel == "update_a_row_notification":
                    self.process_update_event(notify.payload)
            time.sleep(time_to_sleep)
        
        curs.close()
        conn.close()
    def process_insert_event(self, payload):
        # Process the payload received from the trigger event
        # You can implement your custom logic here
        print("INSERT EVENT")
        print("Received trigger event:\n", payload)
        res = json.loads(payload)

        if res["Status"] != "Ready":
            print("Something went wrong. Initial status is not Ready")
            return

        blob = res["File"]
        message = bytearray.fromhex(blob[2:]).decode()
        sender = res["From"]
        policy = res["Policy"].strip('][').split(', ')
        id = res["ID"]
        list_of_entries = res["Entries"].split('], [')
        entries = [i.strip('][').split(', ') for i in list_of_entries]

        process_id = res["Process_id"]

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
            if sender not in self.handshaked_addresses:
                response = requests.post(self.API_URL + "dataOwner/handshake", json=data)
                print(response)
                if response.status_code != 200:
                    print("Something went wrong with the API")
                    return
                self.handshaked_addresses.append(sender)

        conn, curs = self.__create_connnection__()
        
        curs.execute('UPDATE public."CAKE-1" SET "Status" = ' + "'Submitted'" + ' WHERE "ID" ='  + str(res["ID"]))
        conn.commit()

        curs.close()
        conn.close()
        response = requests.post(self.API_URL + "dataOwner/cipher", json=data)
        print(response)

        if response.status_code != 200:
            print("Something went wrong with the API")
            return
        
        print(response.text)

        conn, curs = self.__create_connnection__()
        curs.execute('UPDATE public."CAKE-1" SET "Status" = ' + "'Ciphered'" + ' WHERE "ID" ='  + str(res["ID"]))
        conn.commit()
        curs.close()
        print("Updated the database to Ciphered")

    def process_update_event(self, payload):
        # Process the payload received from the trigger event
        # You can implement your custom logic here
        print("UPDATE EVENT")
        print("Received trigger event:\n", payload)
        res = json.loads(payload)

        if res["Status"] == "Ready":
            self.process_insert_event(payload)
            return
        return
        

# Start listening for trigger events
if __name__ == "__main__":
    speck = SPECK()
    speck.listen_for_trigger_events()


