from irc_lib.protocols.user import User


class NickServRawEvents(object):
#

    def onNSERV_ACC(self, ev):
        if not ev.msg:
            return
        self.bot.loggingq.put(ev)
        snick = ev.msg.split()[0]
        status = ev.msg.split()[1]

        self.locks['NSStatus'].acquire()
        if not snick in self.bot.users:
            self.bot.users[snick] = User(snick)
        self.bot.users[snick].status = int(status)
        self.locks['NSStatus'].notifyAll()
        self.locks['NSStatus'].release()

    def onNSERV_Default(self, ev):
        pass
