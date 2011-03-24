import time
import cmd as cprompt
import urllib
from utils.irc_name import get_nick

from IRCBotBase import IRCBotBase

class TestBot(IRCBotBase, cprompt.Cmd):
    
    def __init__(self, nick='DevBot'):
        IRCBotBase.__init__(self, nick)
        cprompt.Cmd.__init__(self)
    
    def onDefault(self, ev):
        self.printq.put('%s S: %s C: %s T: %s M: %s'%(ev.type.ljust(5), ev.sender.ljust(25), ev.cmd.ljust(15), ev.target, ev.msg))
        pass

    def onCmd(self, ev):
        self.printq.put('%s S: %s C: %s T: %s M: %s'%(ev.type.ljust(5), ev.sender.ljust(25), ev.cmd.ljust(15), ev.target, ev.msg))
        
        if ev.cmd == 'listusers':
            for key, user in self.users.items():
                self.printq.put(user.get_string())

        if ev.cmd == 'ip':
            nick = ev.msg.split()[0].strip()
            ip = self.getIP(nick)
            self.say(ev.sender, 'User %s, %s'%(nick, ip))

        if ev.cmd == 'dcc':
            self.dcc.dcc(ev.sender)

        if ev.cmd == 'loc':
            nick = ev.msg.split()[0].strip()
            ip = self.getIP(nick)
            file, header = urllib.urlretrieve('http://api.ipinfodb.com/v3/ip-city/?key=65aede7e4d8ac7708aad9731fd61c11f7ed2dafdcccd45d3a7b0773c44877c88&ip=%s'%ip) 
            buffer = open(file).read().split(';')
            self.say(ev.sender, 'User %s, IP : %s, Country : %s, City : %s'%(nick, ip, buffer[4], buffer[6]))

    def onJOIN(self, ev):
        if ev.sender == self.cnick:
            self.ctcp.action(ev.chan, 'greets everyone.')
        elif ev.chan != "#test":
            self.irc.privmsg(ev.chan, 'Hello %s!'%ev.sender)
    
            
    def onDCCMsg(self,ev):
        self.dcc.say(ev.sender, ev.msg)

if __name__ == "__main__":
    bot = TestBot('PMDevBot')
    #bot.start()
    bot.connect('irc.esper.net')
    bot.irc.join('#test')


    bot.start()
