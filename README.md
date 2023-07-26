# SPECK - Secrecy and Privacy Enhancer for Ciphered Knowledge
This repository is an extension of the CAKE project, through a postgres db and a python scrypt it is possible to interact with the CAKE API and automate the ciphering of the messages

## Getting Started
### Prerequisites
You must have docker installed on your device
### Lunch postgres db and pgadmin
Open your terminal and run this command in SPECK folder
```bash
docker-compose up
```
At this point your device will have a docker with a server containing a database, with port `5432` exposed, and a second container via the address `http://localhost:5050/` of your browser to use pgAdmin4 and interact with the database.

### Connect pgadmin4 to postgres server 
1. Open pgadmin4 in your browser
2. Insert your email and password (admin@admin.com and root)
3. Right click on `Servers` and select `Register` -> `Server...`
4. Insert a name for the server (es. cakedb) and go to the `Connection` tab
5. Insert has host address the address of the docker container hosting the db in the network cake-network
6. Insert as port `5432`
7. Insert as username `root` and as password `root`

### Lunch the python script
Make sure you have successfully started the CAKE project, that you have launched the API exposing the associated port.

Open the speck.py file and correctly set the CAKE db and api addresses.


Open your terminal and run this command in SPECK folder
```bash
    python speck.py
```