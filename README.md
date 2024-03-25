# Distributed-Key-Value-System


This a centralized distributed key-value storage system that can perform basic functions such as read, write, and delete, supporting multiple users and ensuring data consistency.

## Structure
![image](https://github.com/yanhuojunjun/Distributed-Key-Value-System/assets/149027679/ee652b35-0c76-4343-9aa1-660b3f466517)

central_server.py   -->   central server
server.py           -->   distributed server
client.py           -->   client
server_x_database.sqlite  --> distributed database data


## Usage
1. Execute central_server.py
2. Execute multiple server.py in different terminals
3. Execute client.py, input your username, password, and the server id you want to connect
4. Execute operations in the client terminal, the changes will be updated automatically to all databases.
![image](https://github.com/yanhuojunjun/Distributed-Key-Value-System/assets/149027679/a74c3fd5-effe-4a45-a2ff-189787edf080)

