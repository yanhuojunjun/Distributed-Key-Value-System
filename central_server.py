import socket
import select
import threading
import socket

class CentralServer: #中心服务器类

    def __init__(self, host='localhost', port=21000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)   # 最大排队数是5
        self.client_sockets = []       # 客户端（这里是分布式服务器）列表
        self.stop_server = False


    def broadcast(self, message): #将消息广播给每一个服务器
        for client_socket in self.client_sockets:
            client_socket.send(message)


    def handle_client(self, client_socket): #接收并广播服务器消息
        while True:
            try:
                message = client_socket.recv(1024) #接收来自服务器的更新消息
                if not message:
                    break 
                self.broadcast(message)   #将更新消息广播给所有服务器
            except Exception as e:
                print(f"Error: {e}")
                break

        client_socket.close()
        self.client_sockets.remove(client_socket)


    def start(self): #开始
        print(f"Central server is running on {self.host}:{self.port}")
        while not self.stop_server:
            readable, _, _ = select.select([self.server_socket] + self.client_sockets, [], [])
            for sock in readable:
                if sock == self.server_socket: #新socket加入
                    client_socket, addr = self.server_socket.accept() # 接收
                    self.client_sockets.append(client_socket)         # 加入
                    print(f"Server connected from {addr}")            # 打印
                    #创建并执行一个线程执行handle_client函数，负责监听某个服务器的socket的信息
                    threading.Thread(target=self.handle_client, args=(client_socket,)).start()
                else:    # 有消息可读
                    self.handle_client(sock)

        self.server_socket.close()

 
    def stop(self): #终止
        self.stop_server = True


if __name__ == '__main__': #主函数
    central_server = CentralServer() #创建实例
    try:
        central_server.start() #启动中心服务器
    except KeyboardInterrupt:
        central_server.stop()  #终止中心服务器
