import rpyc  # 用于实现RPC

# 客户端类------------------------
class Client(object):
    
    """
    PUT key value —— Generate or Modify (key, value)
    GET key —— Query (key, value) by the key
    DEL key —— Delete (key, value) by the key
    GETALL —— Get all (key, value) in the database 
    DELALL —— Delete all (key, value) in the database
    """

    # 与本地主机的server端口建立RPC连接
    def connect(self, server):
        self.conn = rpyc.connect('localhost', server)


    # 启动当前客户端
    def run(self):
        try:
            while True:
                #server_choice为1表示选择第一个服务器s1，为2表示选择第二个服务器s2
                server_choice = input("Choose server (1 for s1, 2 for s2): ")
                if server_choice not in ['1', '2']:
                    print("Invalid choice. Please enter 1 or 2.")
                    continue
                
                server = 20000 + int(server_choice) #s1端口是20001，s2端口是20002
                self.connect(server) #让当前客户端与对应服务器端口建立RPC连接
                
                username = input('Please input your username:') #输入用户名
                password = input('Please input your password:') #输入密码

                #远程过程调用服务器中的check函数检查当前用户密码是否正确
                #如果正确则可以进行run-command函数输入指令与服务器互动，正式建立连接
                #如果错误则退出连接
                if self.conn.root.check(username, password) == True: 
                    print(f'\nWelcome to Distributed Key-Value System (Server {server_choice})!\n')
                    print("Enter \"help\" for the list of commands:\n")
                    self.run_commands()
                else:
                    print("Sorry, the username or password is wrong, please try again!")
                    self.conn.close()
        except KeyboardInterrupt:
            pass
    

    #输入执行指令
    def run_commands(self):
        while True:
            command = input(f"Client >> ") # 输入指令
            if command == 'help': # help则输出指令目录
                print(self.__doc__)
            else:                 # 远程过程调用服务器中的function函数执行command指令，并返回msg执行结果
                msg = self.conn.root.function(command)
                print(msg)


if __name__ == '__main__':  #主函数
    client = Client() #实例化客户端
    client.run()      #运行客户端
