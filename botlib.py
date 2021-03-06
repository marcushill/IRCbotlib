#!python3
__author__ = 'mhill'

import socket
import random
import time
import re
import json


class Bot:
    def __init__(self, server, channel, nick, ident):
        self.server = server
        self.channel = channel
        self.nick = nick
        self.triggers = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server, 6667))
        self.sock.recv(2048)
        self.sock.send(("USER " + nick + " " + nick + " " + nick + " : " + ident + "\r\n").encode('utf-8'))
        self.sock.send(("NICK " + nick + "\r\n").encode('utf-8'))
        time.sleep(2)

    def sendmsg(self, chan, msg):
        self.send("PRIVMSG " + chan + " :" + msg + "\r\n")

    def joinchan(self, chan):
        self.send("JOIN " + chan + "\r\n")

    def send(self, msg):
        self.sock.send(msg.encode('utf-8'))

    def recv(self, amount):
        return self.sock.recv(amount).decode('utf-8')

    def action(self, chan, action):
        self.sendmsg(chan, '\x01ACTION ' + action + '\x01')

    def add_trigger(self, trigger):
        self.triggers.append(trigger)

    def users(self):
        #^:(?P<nick>\w+)!~(?P<real>[\w @\.]+)\s*PRIVMSG\s*#(?P<channel>\w+)\s*:ACTION(?P<message>.*)$
        pass
    
    def act(self):
        while True:
            ircmsg = self.recv(2048).strip('\n\r')
            print(ircmsg.encode('utf-8'))
            if ircmsg.find("PING :") != -1:
                pingid = ircmsg.split(':')
                self.send("PONG " + pingid[-1] + "\r\n")
            elif ircmsg.find("IRC.SERVER NOTICE " + self.nick + " :on ") != -1:
                self.joinchan(self.channel)
            else:
                for item in self.triggers:
                    if item.attempt(ircmsg):
                        if item.command:
                            if item.get_response() == 'quit':
                                self.sock.close()
                                return
                        if item.action:
                            self.action(self.channel, item.get_response())
                            break
                        else:
                            self.sendmsg(self.channel, item.get_response())
                            break


class Trigger:
    def __init__(self, pattern, responses, isAction, isCommand, *args):
        self.regex = re.compile(pattern, re.I)
        self.action = isAction
        self.responses = responses
        self.groups = args
        self.command = isCommand

    def attempt(self, message):
        match = self.regex.match(message)
        if match and len(self.groups) > 0:
            for group in self.groups:
                if not group.match(match.group(group.name)):
                    return False
            return True
        elif match:
            return True
        return False

    def get_response(self):
        return random.choice(self.responses)


class Group:
    def __init__(self, group, *args):
        self.name = group
        self.allow = [re.compile(x, re.I) for x in args]

    def match(self, string):
        for item in self.allow:
            if item.match(string):
                return True
        return False

