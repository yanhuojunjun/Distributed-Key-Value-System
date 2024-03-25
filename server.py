import rpyc
from rpyc.utils.server import ThreadedServer
from multiprocessing import Process
from sqlitedict import SqliteDict
import socket
import json
import threading


#服务端类---------------------------------------------------------
class ServerService(rpyc.Service):

    def __init__(self, id, database, central_server_host, central_server_port):
        super().__init__()
        self.id = id                  # id=1表示当前进程是服务器s1
        self.database = database      # 每一个服务器都有一个数据库
        # 连接到中心服务器
        self.central_server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #建立socket
        self.central_server_connection.connect((central_server_host, central_server_port)) #连接


    def send_sync_message(self, action, key, value=None): #将更新动作发送给中心服务器
        #将当前服务器执行的更新动作打包成消息
        message = json.dumps({'action': action, 'key': key, 'value': value, 'server_id': self.id})
        #将消息发送到中心服务器
        self.central_server_connection.send(message.encode('utf-8'))
    

    def start_listen_to_central_server(self): #创建一个线程专门监听中心服务器发送的消息
        #创建一个线程，该线程会执行listen_to_central_server函数中的内容
        self.listen_thread = threading.Thread(target=self.listen_to_central_server)
        #开始执行该线程
        self.listen_thread.start() 


    def listen_to_central_server(self): #监听线程执行的函数
        while True:
            #从与中心服务器建立的socket中接收更新消息
            message = self.central_server_connection.recv(1024).decode('utf-8')
            if message:
                data = json.loads(message)
                #执行process_central_message函数来执行消息的更新内容
                self.process_central_message(data) 


    def process_central_message(self, data): #执行来自中心服务器的更新消息
        action = data['action']        #提取动作
        key = data['key']              #提取键
        value = data.get('value')      #提取值
        server_id = data['server_id']  #提取发出该执行动作的服务器号
        if server_id != self.id:    #如果这个更新行为来自其他服务器，则执行更新操作
            if action == 'Put':   #添加或更新
                self.database[key] = value
            elif action == 'Del': #删除
                if key in self.database:
                    del self.database[key]
            elif action == 'DelAll': #全部删除
                self.database.clear()
    

    def on_connect(self, conn): #有客户端与当前服务器连接时触发
        print(f"Client connected to server {self.id}")


    def on_disconnect(self, conn): #有客户端与当前服务器断开连接时触发
        print(f"Client disconnected from server {self.id}")


    def Put(self, key, value): # PUT操作
        self.database[key] = value # 更新数据库内容
        self.send_sync_message('Put', key, value) #将更新操作发给中心服务器
        return f"Key '{key}' updated with value '{value}' on server {self.id}" #返回执行结果信息


    def Get(self, key): # GET操作
        return self.database.get(key, None) #返回数据库中key对应的值

 
    def Delete(self, key): # DEL操作
        if key in self.database:
            del self.database[key]                              #删除
            self.send_sync_message('Del', key)                  #将删除操作发给中心服务器
            return f"Key '{key}' deleted from server {self.id}" #返回删除成功
        return f"Key '{key}' not found on server {self.id}"     #返回删除失败


    def Get_All(self): # Get_All操作
        return list(self.database.items()) #返回数据库中所有的值


    def Delete_All(self): # DEL_ALL操作
        self.database.clear()                             # 删除
        self.send_sync_message('DelAll', None)            # 将删除操作发给中心服务器
        return f"All keys deleted from server {self.id}"  # 返回删除信息

   
    #exposed表示该函数可以被RPC连接的远程主机调用，客户端会远程调用该函数执行相关操作
    #在客户端中通过self.conn.root.function(clause)调用
    #在函数内部就是通过调用上面相关操作的函数来实现相关操作
    def exposed_function(self, clause):
        clause = clause.strip().split()
        lens = len(clause)
        WRONG_MSG = 'Wrong command. Enter help if necessary.'
        if lens < 1:
            return WRONG_MSG
        command = clause[0].lower()

        if command == 'put':
            if lens == 3:
                key = clause[1]
                value = clause[2]
                return self.Put(key, value)
            else:
                return WRONG_MSG

        if command == 'get':
            if lens == 2:
                key = clause[1]
                result = self.Get(key)
            else:
                return WRONG_MSG

            if result == None:
                return 'Key %s not found.' %key
            else:
                return result

        if command == 'getall':
            if lens == 1:
                return self.Get_All()
            else:
                return WRONG_MSG

        if command == 'del':
            if lens == 2:
                key = clause[1]
                return self.Delete(key)
            else:
                return WRONG_MSG

        if command == 'delall':
            if lens == 1:
                return self.Delete_All()
            else:
                return WRONG_MSG


    #exposed表示该函数可以被RPC连接的远程主机调用，客户端会远程调用该函数检查用户密码是否正确
    #在客户端中通过self.conn.root.check(username,password)调用
    #在函数内部就是通过调用服务器本地的user列表查看用户名密码是否正确
    def exposed_check(self,username,password):

        users = {}
        with open('./user.txt') as file: #从服务器下的user.txt文件中获取用户密码信息
            for i in file.readlines():
                i = i.split()
                users[i[0]] = i[1]

        if username in users.keys() and users[username] == password:
            return True    #如果正确返回true
        else:
            return False   #如果错误返回false



def start_servers(num_servers, start_port=20000): #生成num-servers个进程，一个进程就是一个分布式服务器
    servers = []
    for i in range(1, num_servers + 1): 
        port = start_port + i                                              #服务器进程端口号
        server_process = Process(target=server_function, args=(i, port))   #创建一个子进程，该进程执行server-function函数
        server_process.start()                                             #启动服务器进程
        servers.append(server_process)                                     #将进程加入到服务器列表中

    for server in servers: #阻塞，全部服务器进程结束后才继续执行主进程
        server.join()


def server_function(id, port, central_server_host='localhost', central_server_port=21000): #服务器进程执行的函数
    database_path = f'./server_{id}_database.sqlite'   # 创建一个属于该进程的服务器
    with SqliteDict(database_path, autocommit=True) as database:
        #创建了一个服务器类实例，传递了该服务器的数据库，id，中心服务器信息
        service = ServerService(id, database, central_server_host, central_server_port) 
        #启动该服务器进程中的监听线程
        service.start_listen_to_central_server() 
        #将服务器与端口绑定在一起
        server = ThreadedServer(service, port=port, protocol_config={'allow_all_attrs': True})
        #输出启动信息
        print(f"Starting server {id} on port {port}")
        #启动服务器
        server.start()


if __name__ == '__main__':  #主函数
    start_servers(2)  # 生成两个服务器进程，这里可以修改
