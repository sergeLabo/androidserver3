# androidserver3

Un serveur de jeu en TCP (et Multicast) sur un réseau local.

## Réalisé avec Kivy, Twisted et compilé avec Buildozer

## Compilation impossible en Mars 2018


### Python 3.5
Sur debian strectch 9.4

Buildozer n'aime pas Twisted ni en python 2.7, ni en 3.5,

[asyncio](https://docs.python.org/3/library/asyncio.html) est utilisé à partir de l'exemple de la doc:

* [simple_tcp_server.py
](https://github.com/python/asyncio/blob/master/examples/simple_tcp_server.py)
* [TCP echo server protocol](https://docs.python.org/3/library/asyncio-protocol.html#tcp-echo-server-protocol)
* [TCP echo client using streams](https://docs.python.org/3/library/asyncio-stream.html#tcp-echo-client-using-streams)
### Quelle version de l'interpréteur python ?

[Conseil de la doc Kivy sur Cython](https://kivy.org/docs/installation/installation-linux.html#cython)

Résumé: ça marchera ou pas !

J'ai réussi avec
 sudo pip install Cython==0.23

### Buildozer requirements

 requirements = kivy


### Bugs connu

### Merci à
* [La Labomedia](https://labomedia.org/)
* [Le Centre Ressources](https://wiki.labomedia.org/index.php/Accueil)
* [Les Open Ateliers](https://openatelier.labomedia.org/)
* [Le FabLab Atelier du C01N](https://atelierduc01n.labomedia.org/)
