import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
import json
import requests

TIME_TO_SLEEP = 0.1
HOST_IP = "172.18.0.3"
CHECK_ALREDY_READY = True
API_URL = "http://0.0.0.0:8888/"
DATA_OWNER_HANDSHAKE = False
handshaked_addresses = []

def listen_for_trigger_events():
    conn = psycopg2.connect(
        host=HOST_IP,
        port = 5432,
        database="cake-db",
        user="root",
        password="root"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    curs = conn.cursor()
    
    # Enable LISTEN/NOTIFY for the trigger events
    curs.execute("LISTEN update_a_row_notification;")
    curs.execute("LISTEN update_notification;")

    if CHECK_ALREDY_READY:
        curs.execute('UPDATE public."CAKE-1" SET "Status"='+"'Ready'" +'WHERE "Status"='+"'Ready';")
        conn.commit()
    print("Waiting for trigger events...")
    # TODO: Check if some Ready rows are already in the database
    while True:
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            if notify.channel == "update_notification":
                process_insert_event(notify.payload)
            elif notify.channel == "update_a_row_notification":
                process_update_event(notify.payload)
        time.sleep(TIME_TO_SLEEP)
    
    curs.close()
    conn.close()


def process_insert_event(payload):
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

    #file = blob.decode('UTF-8')

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

    if DATA_OWNER_HANDSHAKE:
        if sender not in handshaked_addresses:
            response = requests.post(API_URL + "dataOwner/handshake", json=data)
            print(response)
            if response.status_code != 200:
                print("Something went wrong with the API")
                return
            handshaked_addresses.append(sender)

    conn = psycopg2.connect(
        host=HOST_IP,
        port = 5432,
        database="cake-db",
        user="root",
        password="root"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    curs = conn.cursor()
    
    curs.execute('UPDATE public."CAKE-1" SET "Status" = ' + "'Submitted'" + ' WHERE "ID" ='  + str(res["ID"]))
    conn.commit()
    response = requests.post(API_URL + "dataOwner/cipher", json=data)
    print(response)

    if response.status_code != 200:
        print("Something went wrong with the API")
        return
    
    print(response.text)

    #TODO: Update the database
    conn = psycopg2.connect(
        host=HOST_IP,
        port = 5432,
        database="cake-db",
        user="root",
        password="root",
    )
    curs = conn.cursor()
    curs.execute('UPDATE public."CAKE-1" SET "Status" = ' + "'Ciphered'" + ' WHERE "ID" ='  + str(res["ID"]))
    conn.commit()
    curs.close()
    print("Updated the database to Ciphered")
    

def process_update_event(payload):
    # Process the payload received from the trigger event
    # You can implement your custom logic here
    print("UPDATE EVENT")
    print("Received trigger event:\n", payload)
    res = json.loads(payload)

    if res["Status"] == "Ready":
        process_insert_event(payload)
        return
    return

# Start listening for trigger events
listen_for_trigger_events()


