#! /bin/bash

g++ -Wall -fexceptions -g -Iinclude -c /home/buccaneersdan/Dokumente/Projekte/Python/ChanMan/DecryptSQLite/src/FileInOut.cpp -o obj/Debug/src/FileInOut.o
g++ -Wall -fexceptions -g -Iinclude -c /home/buccaneersdan/Dokumente/Projekte/Python/ChanMan/DecryptSQLite/main.cpp -o obj/Debug/main.o
g++  -o bin/Debug/DecryptSQLite obj/Debug/main.o obj/Debug/src/FileInOut.o

cp bin/Debug/DecryptSQLite ../tvplugins/Panasonic/DecryptSQLite

chmod ug+x ../tvplugins/Panasonic/DecryptSQLite