#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


"""sans twisted, avec asyncio, en python3"""


import os
import sys
import subprocess
from time import time, sleep
import threading
import json
import ast
import asyncio
import asyncio.streams


import kivy
kivy.require('1.10.0')
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty

from labconfig3 import MyConfig
from tools import datagram_decode, get_ip_address
from labmulticast import Multicast


class MulticastIpSender(Multicast):
    
        
    def __init__(self, ip, port):  #, **kwargs):
 
        # python2
        #super(MulticastIpSender, self).__init__(ip, port, **kwargs)
        
        # python3
        super().__init__()
        
        # ("224.0.0.11", 18888)
        self.multi_addr = ip, port
    
    def get_conf(self):
        """Retourne la tempo de la boucle de Clock."""

        config = AndroidServerApp.get_running_app().config
        freq = int(config.get('network', 'freq'))
        
    def ip_send(self):
        
        mcast = {"Ip Adress": (tcp_ip, tcp_port)}
        resp = json.dumps(mcast).encode("utf-8")
        
        while 1:
            sleep(1)
            
            # j'envoie
            print("Envoi")
            my_multicast.send_to(resp, self.multi_addr)
            sleep(0.01)
            
            # je recois
            data = my_multicast.receive()
            print("Réception:", data)

    def ip_send_thread(self):
        thread_s = threading.Thread(target=self.p_send)
        thread_s.start()
        
        
class MyServer:
    """My TCP server"""

    def __init__(self):
        """this keeps track of all the clients that connected to our
        server.  It can be useful in some cases, for instance to
        kill client connections or to broadcast some data to all
        clients...
        """
        # encapsulates the server sockets
        self.server = None

        # task -> (reader, writer)
        self.clients = {} 

    def _accept_client(self, client_reader, client_writer):
        """This method accepts a new client connection and creates
        a Task to handle this client. 
        self.clients is updated to keep track of the new client.
        """

        # start a new Task to handle this specific client connection
        task = asyncio.Task(self._handle_client(client_reader,
                                                client_writer))
                                                
        self.clients[task] = (client_reader, client_writer)

        def client_done(task):
            print("client task done:", task, file=sys.stderr)
            del self.clients[task]

        task.add_done_callback(client_done)

    @asyncio.coroutine
    def _handle_client(self, client_reader, client_writer):
        """This method actually does the work to handle the requests for
        a specific client.  The protocol is line oriented, so there is
        a main loop that reads a line with a request and then sends
        out one or more lines back to the client with the result.
        """
        
        while True:
            data = (yield from client_reader.readline()).decode("utf-8")
            
            # an empty string means the client disconnected
            if not data: 
                break
                
            cmd, *args = data.rstrip().split(' ')
            if cmd == 'add':
                arg1 = float(args[0])
                arg2 = float(args[1])
                retval = arg1 + arg2
                client_writer.write("{!r}\n".format(retval).encode("utf-8"))
            elif cmd == 'repeat':
                times = int(args[0])
                msg = args[1]
                client_writer.write("begin\n".encode("utf-8"))
                for idx in range(times):
                    client_writer.write("{}. {}\n".format(idx+1, msg)
                                        .encode("utf-8"))
                client_writer.write("end\n".encode("utf-8"))
            else:
                print("Bad command {!r}".format(data), file=sys.stderr)

            # This enables us to have flow control in our connection.
            yield from client_writer.drain()

    def start(self, loop):
        """Starts the TCP server, so that it listens on port 12345.

        For each client that connects, the accept_client method gets
        called.  This method runs the loop until the server sockets
        are ready to accept connections.
        """
        
        coro = asyncio.streams.start_server(self._accept_client,
                                            '127.0.0.1', 
                                            12345,
                                            loop=loop)
        print("start", loop)
        self.server = loop.run_until_complete(coro)
        
        # Serve requests until Ctrl+C is pressed
        addr = self.server.sockets[0].getsockname()
        print('Serving on {}'.format(addr))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self.stop(loop)
    
    def stop(self, loop):
        """Stops the TCP server, i.e. closes the listening socket(s).
        This method runs the loop until the server sockets are closed.
        """
        
        if self.server is not None:
            self.server.close()
            loop.run_until_complete(self.server.wait_closed())
            self.server = None


class MainScreen(Screen):
    """Ecran principal"""

    info = StringProperty()
    
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        
        self.display_info_thread()
        print("Initialisation de MainScreen ok")
        
        # Construit le réseau, tourne tout le temps
        scr_manager = self.get_screen_manager()
        
        # existe dans AndroidServerApp !
        #self.server = MyServer(scr_manager)
        
    def get_screen_manager(self):
        return AndroidServerApp.get_running_app().screen_manager
        
    def display_info(self):
        while 1:
            sleep(1)
            print(self.info)
            self.info = "test" + "\n" + "toto"

    def display_info_thread(self):
        thread_d = threading.Thread(target=self.display_info)
        thread_d.start()

    
SCREENS = { 0: (MainScreen, "Main")}


class AndroidServerApp(App):
    
    def build(self):
        """Exécuté en premier après run()"""
        
        # Creation des ecrans
        self.screen_manager = ScreenManager()
        for i in range(len(SCREENS)):
            self.screen_manager.add_widget(SCREENS[i][0](name=SCREENS[i][1]))

        return self.screen_manager

    def on_start(self):
        """Exécuté apres build()"""
            
        # Lancement asyncio
        main()
        
        # Lancement multicast
        MulticastIpSender()
        
    def build_config(self, config):
        """Si le fichier *.ini n'existe pas,
        il est créé avec ces valeurs par défaut.
        Si il manque seulement des lignes, il ne fait rien !
        """

        config.setdefaults('network',
                            { 'multi_ip': '221.0.0.11',
                              'multi_port': '18888',
                              'tcp_port': '8000',
                              'freq': '60'})

        config.setdefaults('kivy',
                            { 'log_level': 'debug',
                              'log_name': 'androidserver_%y-%m-%d_%_.txt',
                              'log_dir': '/toto',
                              'log_enable': '1'})

        config.setdefaults('postproc',
                            { 'double_tap_time': 250,
                              'double_tap_distance': 20})

    def build_settings(self, settings):
        """Construit l'interface de l'écran Options,
        pour  le serveur seul, Kivy est par défaut,
        appelé par app.open_settings() dans .kv
        """

        data = """[{"type": "title", "title":"Configuration du réseau"},
                      {"type": "numeric",
                      "title": "Fréquence",
                      "desc": "Fréquence entre 1 et 60 Hz",
                      "section": "network", "key": "freq"}
                   ]"""

        # self.config est le config de build_config
        settings.add_json_panel('AndroidServer', self.config, data=data)

    def on_config_change(self, config, section, key, value):
        """Si modification des options, fonction appelée automatiquement
        """

        freq = int(self.config.get('network', 'freq'))
        menu = self.screen_manager.get_screen("Main")

        if config is self.config:
            token = (section, key)

            # If frequency change
            if token == ('network', 'freq'):
                # TODO recalcul tempo
                print("Nouvelle fréquence", freq)

    def go_mainscreen(self):
        """Retour au menu principal depuis les autres écrans."""

        #if touch.is_double_tap:
        self.screen_manager.current = ("Main")

    def do_quit(self):

        print("Je quitte proprement")

        # Kivy
        AndroidServerApp.get_running_app().stop()

        # Extinction de tout
        os._exit(0)


def always(server, loop):
    thread_msg = threading.Thread(target=server_thread,
                                  args=(server, loop,))
    thread_msg.start()
        
def server_thread(server, loop):
    server.start(loop)
        
def main():
    loop = asyncio.get_event_loop()

    # creates a server and starts listening to TCP connections
    server = MyServer()
    always(server, loop)


if __name__ == "__main__":
    AndroidServerApp().run()
