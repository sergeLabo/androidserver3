#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


import ast
import subprocess


def get_ip_address():
    """La commande en terminal:
    hostname -I
    retourne l'ip locale !!
    """
    
    try:
        IP_CMD = "hostname -I"
        
        ip_long = subprocess.check_output(IP_CMD, shell=True)
        ip = ip_long.decode("utf-8")
        # espace\n à la fin à couper
        ip = ip[:-2]

    except:
        ip = "192.168.1.4"
    print("IP = {} de type {} len {}".format(ip, 
                                               type(ip),
                                               len(ip)))

    return ip

def datagram_decode(data):
    """Decode le message.
    Retourne un dict ou None
    """

    try:
        dec = data.decode("utf-8")
    except:
        #print("Décodage UTF-8 impossible")
        dec = data

    try:
        msg = ast.literal_eval(dec)
    except:
        #print("ast.literal_eval impossible")
        msg = dec

    if isinstance(msg, dict):
        return msg
    else:
        #print("Message reçu: None")
        return None

if __name__ == "__main__":
    
    get_ip_address()
