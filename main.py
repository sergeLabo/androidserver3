#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


"""
sans twisted, avec asyncio, en python3

AndroidServerApp ---------> config
        |
      crée
        |
        MainScreen
                | 
               crée
                |       
               Game
                 | 
              hérite de
                 |                    
                MyTCPServerFactory et de MulticastIpSender
                    | 
                  hérite de
                    |                  
                  MyTCPServer

doc lien donné par doc officielle sur super()
https://rhettinger.wordpress.com/2011/05/26/super-considered-super/

"""


import os
import sys
import subprocess
from time import time, sleep
import threading
import json

import asyncio
import asyncio.streams

import kivy
kivy.require('1.10.0')
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from kivy.clock import Clock

from tools import datagram_decode, get_ip_address
from labmulticast import Multicast


class MulticastIpSender(Multicast):
    
    def __init__(self, config):
        
        print("Lancement de la boucle Multicast")
        self.config = config
        self.multi_ip = self.config.get('network', 'multi_ip')
        self.multi_port = int(self.config.get('network', 'multi_port'))
        self.multi_addr = self.multi_ip, self.multi_port
        print("Adresse Multicast:", self.multi_addr)
        
        super().__init__(self.multi_ip, self.multi_port)
        
        # Lancement de l'envoi permanent
        self.ip_send_thread()
        
    def ip_send(self):
        tcp_ip = get_ip_address()
        tcp_port = int(self.config.get('network', 'tcp_port'))
        
        m = {"TCP Adress": (tcp_ip, tcp_port)}
        msg = json.dumps(m).encode("utf-8")
        
        while 1:
            #print("Envoi de ", m)
            sleep(1)
            self.send_to(msg, self.multi_addr)

    def ip_send_thread(self):
        thread_s = threading.Thread(target=self.ip_send)
        thread_s.start()
        
        
class MyTCPServer:
    """My TCP server"""

    def __init__(self, config):
        """this keeps track of all the clients that connected to our
        server.  It can be useful in some cases, for instance to
        kill client connections or to broadcast some data to all
        clients...
        """
        
        print("Lancement de la boucle TCP")
        
        self.tcp_port = int(config.get('network', 'tcp_port')) 
        self.tcp_ip = get_ip_address()
        
        # encapsulates the server sockets
        self.server = None

        # task -> (reader, writer)
        self.clients = {} 
        
        # Le message reçu en TCP
        self.recv = ""
        
    def _accept_client(self, client_reader, client_writer):
        """This method accepts a new client connection and creates
        a Task to handle this client. 
        self.clients is updated to keep track of the new client.
        """

        # start a new Task to handle this specific client connection
        task = asyncio.Task(self._handle_client(client_reader, client_writer))
                                                
        self.clients[task] = (client_reader, client_writer)
        print("Client accepté")
        
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
        
        print("Réception:")
        while True:
            
            # Les envois se finnissent toujours par \n
            d = yield from client_reader.readline()
            data = d.decode("utf-8")
            #print("Reception de:", data)
            self.recv = data[:-1]
                
            if not data: 
                self.recv = ""
                print("Pas de data reçues") 
                break
                
            cmd, *args = data.rstrip().split(' ')

            if cmd == 'add':
                arg1 = float(args[0])
                arg2 = float(args[1])
                retval = arg1 + arg2
                print("Somme des arguments = ", retval)
                r = "{!r}\n".format(retval).encode("utf-8")
                client_writer.write(r)
                
            elif cmd == 'repeat':
                times = int(args[0])
                msg = args[1]
                client_writer.write("begin\n".encode("utf-8"))
                for idx in range(times):
                    client_writer.write("{}. {}\n".format(idx+1, msg)
                                        .encode("utf-8"))
                client_writer.write("end\n".encode("utf-8"))
                
            else:
                pass
                #print("Bad command {!r}".format(data), file=sys.stderr)

            # This enables us to have flow control in our connection.
            yield from client_writer.drain()

    def start(self, loop):
        """Starts the TCP server, so that it listens on port 8000.

        For each client that connects, the accept_client method gets
        called.  This method runs the loop until the server sockets
        are ready to accept connections.
        """
        
        
        coro = asyncio.streams.start_server(self._accept_client,
                                            self.tcp_ip, 
                                            self.tcp_port,
                                            loop=loop)
        print("start", loop)
        self.server = loop.run_until_complete(coro)
        
        # Serve requests until Ctrl+C is pressed
        addr = self.server.sockets[0].getsockname()
        print('\nServing on {}\n'.format(addr))
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


class MyTCPServerFactory:
    
    def __init__(self, config):
        print("Lancement de l'usine TCP")
        self.tcp_main(config)
        
    def worker(self, loop):
        """Il faut bien que quelqu'un travaille"""
        
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.server.start(loop))

    def tcp_main(self, config):
        self.server = MyTCPServer(config)
        loop = asyncio.new_event_loop()
        wt = threading.Thread(target=self.worker, args=(loop,))
        wt.start() 
        
#class Game(MulticastIpSender, MyTCPServerFactory):
class Game(MyTCPServerFactory):
    def __init__(self, config):
        super(Game, self).__init__(config)
        
        self.config = config
        
        freq = int(self.config.get('network', 'freq'))      
        tempo = 1 / freq
        print("Rafraississement du jeu tous les", tempo)
        self.event = Clock.schedule_interval(self.game_update, tempo)
        
    def game_update(self, dt):
        if self.server.recv:
            print("\nRéception de:", self.server.recv)
            sm = self.get_screen_manager()
            sm.current_screen.info = self.server.recv
        
    def get_screen_manager(self):
        return AndroidServerApp.get_running_app().screen_manager
    
    
class MainScreen(Screen):
    """Ecran principal"""

    info = StringProperty()
    
    def __init__(self, **kwargs): 
        """
        def __init__(self, **kwargs):
            super(MainScreen, self).__init__(**kwargs)
        """
        
        super().__init__(**kwargs)
        
        ip = "224.0.0.11"
        port = 18888
        
        # Récup config
        self.config = AndroidServerApp.get_running_app().config
        
        # L'objet jeu
        self.game = Game(self.config)
        
        print("Initialisation de MainScreen ok")

    
SCREENS = { 0: (MainScreen, "Main")}


class AndroidServerApp(App):
    
    def build(self, **kwargs):
        """Exécuté en premier après run()"""
                
        # Creation des ecrans
        self.screen_manager = ScreenManager()
        for i in range(len(SCREENS)):
            self.screen_manager.add_widget(SCREENS[i][0](name=SCREENS[i][1]))

        return self.screen_manager

    def on_start(self):
        """Exécuté apres build()"""
        pass
        
    def build_config(self, config):
        """Si le fichier *.ini n'existe pas,
        il est créé avec ces valeurs par défaut.
        Si il manque seulement des lignes, il ne fait rien !
        """

        config.setdefaults('network',
                            { 'multi_ip': '224.0.0.11',
                              'multi_port': '18888',
                              'tcp_port': '8000',
                              'freq': '1'})

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

        data =  """[{"type": "title", "title":"Réseau"},
                            {  "type":    "numeric",
                                "title":   "Fréquence",
                                "desc":    "Fréquence entre 1 et 60 Hz",
                                "section": "network", 
                                "key":     "freq"},
                             
                    {"type": "title", "title":"Réseau"},
                            {   "type":    "string",
                                "title":   "IP Multicast",
                                "desc":    "IP Multicast",
                                "section": "network", 
                                "key":     "multi_ip"},
                                
                    {"type": "title", "title":"Réseau"},
                            {   "type":    "numeric",
                                "title":   "Port Multicast",
                                "desc":    "Port Multicast",
                                "section": "network", 
                                "key":     "multi_port"},
                                
                    {"type": "title", "title":"Réseau"},
                            {   "type":    "numeric",
                                "title":   "TCP Port",
                                "desc":    "TCP Port",
                                "section": "network", 
                                "key":     "tcp_port"}
                    ]
                """

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


if __name__ == "__main__":
    AndroidServerApp().run()


    # #def get_conf(self):
        # #"""Retourne la tempo de la boucle de Clock."""

        # #config = AndroidServerApp.get_running_app().config
        # #freq = int(config.get('network', 'freq'))

    # #def get_screen_manager(self):
        # #return AndroidServerApp.get_running_app().screen_manager
