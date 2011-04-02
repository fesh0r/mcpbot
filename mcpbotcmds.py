import sqlite3
import time
import string
import csv
import threading
from irc_lib.utils.restricted import restricted
from database import database

class MCPBotCmds(object):
    def cmdDefault(self, sender, chan, cmd, msg):
        pass

    #================== Base chatting commands =========================
    @restricted(4)
    def cmd_say(self, sender, chan, cmd, msg, *args, **kwargs):
        if not len(msg.split()) > 1: return
        self.say(msg.split()[0], ' '.join(msg.split()[1:]))

    @restricted(4)
    def cmd_msg(self, sender, chan, cmd, msg, *args, **kwargs):
        if not len(msg.split()) > 1: return
        self.irc.privmsg(msg.split()[0], ' '.join(msg.split()[1:]))

    @restricted(4)
    def cmd_notice(self, sender, chan, cmd, msg, *args, **kwargs):
        if not len(msg.split()) > 1: return
        self.irc.notice(msg.split()[0], ' '.join(msg.split()[1:]))

    @restricted(4)
    def cmd_action(self, sender, chan, cmd, msg, *args, **kwargs):
        if not len(msg.split()) > 1: return
        self.ctcp.action(msg.split()[0], ' '.join(msg.split()[1:]))

    @restricted(4)      
    def cmd_pub(self, sender, chan, cmd, msg, *args, **kwargs):
        cmd = msg.split()[0]
        if len(msg.split()) > 1:
            msg = ' '.join(msg.split()[1:])

        cmd = cmd.lower()
        
        if cmd in ['ssf, ssm, scf, scm']:
            self.say(sender, 'No public setters !')
            return
        
        try:
            getattr(self, 'cmd_%s'%cmd )(chan, chan, cmd, msg)
        except AttributeError:
            getattr(self, 'cmdDefault')(chan, chan, cmd, msg)
        
    #===================================================================

    #================== Getters classes ================================
    def cmd_gcc(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bgcc <classname>$N              : Get Client Class."""
        self.getClass(sender, chan, cmd, msg, 'client')

    def cmd_gsc(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bgsc <classname>$N              : Get Server Class."""
        self.getClass(sender, chan, cmd, msg, 'server')

    def cmd_gc(self, sender, chan, cmd, msg, *args, **kwargs):
        self.getClass(sender, chan, cmd, msg, 'client')        
        self.getClass(sender, chan, cmd, msg, 'server')

    @database
    def getClass(self, sender, chan, cmd, msg, side, *args, **kwargs):
        c         = kwargs['cursor']
        idversion = kwargs['idvers']
        side_lookup = {'client':0, 'server':1}
        msg = msg.strip()
        c.execute("""SELECT name, notch, supername FROM vclasses WHERE (name = ? OR notch = ?) AND side = ? AND versionid = ?""", (msg, msg, side_lookup[side], idversion))
        
        classresults = c.fetchall()
        
        if not classresults:
            self.say(sender, "$B[ GET %s CLASS ]"%side.upper())
            self.say(sender, " No results found for $B%s"%msg)
        
        for classresult in classresults:
            name, notch, supername = classresult

            c.execute("""SELECT sig, notchsig FROM vconstructors WHERE (name = ? OR notch = ?) AND side = ? AND versionid = ?""",(msg, msg, side_lookup[side], idversion))
            constructorsresult = c.fetchall()

            self.say(sender, "$B[ GET %s CLASS ]"%side.upper())
            self.say(sender, " Side        : $B%s"%side)
            self.say(sender, " Name        : $B%s"%name)
            self.say(sender, " Notch       : $B%s"%notch)
            self.say(sender, " Super       : $B%s"%supername)

            for constructor in constructorsresult:
                self.say(sender, " Constructor : $B%s$N | $B%s$N"%(constructor[0], constructor[1]))

    #===================================================================

    #================== Getters members ================================
    def cmd_gcm(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bgcm [classname.]<methodname>$N : Get Client Method."""
        self.outputMembers(sender, chan, cmd, msg, 'client', 'methods')

    def cmd_gsm(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bgsm [classname.]<methodname>$N : Get Server Method."""
        self.outputMembers(sender, chan, cmd, msg, 'server', 'methods')

    def cmd_gm(self, sender, chan, cmd, msg, *args, **kwargs):
        self.outputMembers(sender, chan, cmd, msg, 'client', 'methods')        
        self.outputMembers(sender, chan, cmd, msg, 'server', 'methods')

    def cmd_gcf(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bgcf [classname.]<fieldname>$N  : Get Client Field."""
        self.outputMembers(sender, chan, cmd, msg, 'client', 'fields')

    def cmd_gsf(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bgsf [classname.]<fieldname>$N  : Get Server Field."""
        self.outputMembers(sender, chan, cmd, msg, 'server', 'fields')

    def cmd_gf(self, sender, chan, cmd, msg, *args, **kwargs):
        self.outputMembers(sender, chan, cmd, msg, 'client', 'fields')        
        self.outputMembers(sender, chan, cmd, msg, 'server', 'fields')

    @database
    def outputMembers(self, sender, chan, cmd, msg, side, etype, *args, **kwargs):
        c         = kwargs['cursor']
        idversion = kwargs['idvers']
        side_lookup = {'client':0, 'server':1}
        type_lookup = {'fields':'field', 'methods':'func'}
        msg = msg.strip()

        cname = ''
        mname = ''
        sname = ''
        searchpattern = ''

        tmpmsg = msg

        if len(tmpmsg.split('.')) > 2 or len(tmpmsg.split()) > 2 or not tmpmsg:
            self.say(sender, "$B[ GET %s %s ]"%(side.upper(),etype.upper()))
            self.say(sender, " Syntax error. Use $B%s <membername>$N or $B%s <classname>.<membername>$N"%(cmd,cmd))
            return

    
        if len(tmpmsg.split()) == 2:   #Do we have a signature to search for
            sname    = tmpmsg.split()[1]
            tmpmsg   = tmpmsg.split()[0]

        if len(tmpmsg.split('.')) == 2:
            cname = tmpmsg.split('.')[0]
            mname = tmpmsg.split('.')[1]

        else:
            mname = tmpmsg

        if cname and sname:
            c.execute("""SELECT m.name, m.notch, m.searge, m.sig, m.notchsig, m.desc, m.classname, m.classnotch FROM v%s m
                         WHERE ((m.searge LIKE ? ESCAPE '!') OR m.searge = ? OR m.notch = ? OR m.name = ?) 
                         AND m.side = ? AND m.versionid = ?
                         AND (m.classname = ? OR m.classnotch = ?)
                         AND (m.sig = ? OR m.notchsig = ?)
                         """%etype, 
                         ('%s!_%s!_%%'%(type_lookup[etype],mname),mname,mname,mname,side_lookup[side], idversion, cname, cname, sname, sname))
                         
        elif cname and not sname:
            c.execute("""SELECT m.name, m.notch, m.searge, m.sig, m.notchsig, m.desc, m.classname, m.classnotch FROM v%s m
                         WHERE ((m.searge LIKE ? ESCAPE '!') OR m.searge = ? OR m.notch = ? OR m.name = ?) 
                         AND m.side = ? AND m.versionid = ?
                         AND (m.classname = ? OR m.classnotch = ?)
                         """%etype, 
                         ('%s!_%s!_%%'%(type_lookup[etype],mname),mname,mname,mname,side_lookup[side], idversion, cname, cname))

        elif not cname and sname:
            c.execute("""SELECT m.name, m.notch, m.searge, m.sig, m.notchsig, m.desc, m.classname, m.classnotch FROM v%s m
                         WHERE ((m.searge LIKE ? ESCAPE '!') OR m.searge = ? OR m.notch = ? OR m.name = ?) 
                         AND m.side = ? AND m.versionid = ?
                         AND (m.sig = ? OR m.notchsig = ?)
                         """%etype, 
                         ('%s!_%s!_%%'%(type_lookup[etype],mname),mname,mname,mname,side_lookup[side], idversion, sname, sname))

        else:
            c.execute("""SELECT m.name, m.notch, m.searge, m.sig, m.notchsig, m.desc, m.classname, m.classnotch FROM v%s m
                         WHERE ((m.searge LIKE ? ESCAPE '!') OR m.searge = ? OR m.notch = ? OR m.name = ?) 
                         AND m.side = ? AND m.versionid = ?
                         """%etype, 
                         ('%s!_%s!_%%'%(type_lookup[etype],mname),mname,mname,mname,side_lookup[side], idversion))
                         
        results = c.fetchall()

        if sender in self.dcc.sockets and self.dcc.sockets[sender]:
            lowlimit  = 10
            highlimit = 999
        else:
            lowlimit  = 1
            highlimit = 10

        if len(results) > highlimit:
            self.say(sender, "$B[ GET %s %s ]"%(side.upper(),etype.upper()))
            self.say(sender, " $BVERY$N ambiguous request $R'%s'$N"%msg)
            self.say(sender, " Found %s possible answers"%len(results))        
            self.say(sender, " Not displaying any !")        
        elif highlimit >= len(results) > lowlimit:
            self.say(sender, "$B[ GET %s %s ]"%(side.upper(),etype.upper()))
            self.say(sender, " Ambiguous request $R'%s'$N"%msg)
            self.say(sender, " Found %s possible answers"%len(results))
            maxlencsv   = max(map(len, ['%s.%s'%(result[6], result[0])   for result in results]))
            maxlennotch = max(map(len, ['[%s.%s]'%(result[7], result[1]) for result in results]))
            for result in results:
                name, notch, searge, sig, notchsig, desc, classname, classnotch = result
                fullcsv   = '%s.%s'%(classname, name)
                fullnotch = '[%s.%s]'%(classnotch, notch)
                self.say(sender, " %s %s %s %s"%(fullcsv.ljust(maxlencsv+2), fullnotch.ljust(maxlennotch+2), sig, notchsig))
        elif lowlimit >= len(results) > 0:
            for result in results:
                name, notch, searge, sig, notchsig, desc, classname, classnotch = result
                self.say(sender, "$B[ GET %s %s ]"%(side.upper(),etype.upper()))
                self.say(sender, " Side        : $B%s"%side)
                self.say(sender, " Name        : $B%s.%s"%(classname, name,))
                self.say(sender, " Notch       : $B%s.%s"%(classnotch, notch,))
                self.say(sender, " Searge      : $B%s"%searge)
                self.say(sender, " Type/Sig    : $B%s$N | $B%s$N"%(sig,notchsig))
                if desc:      
                    self.say(sender, " Description : %s"%desc)
        else:
            self.say(sender, "$B[ GET %s %s ]"%(side.upper(),etype.upper()))
            self.say(sender, " No result for %s"%msg)
            c.close()
            return
        
    #===================================================================

    #====================== Search commands ============================
    @database
    def cmd_search(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bsearch <pattern>$N  : Search for a pattern."""        

        c         = kwargs['cursor']
        idversion = kwargs['idvers']

        msg.strip()
        type_lookup = {'method':'func','field':'field'}
        side_lookup = {'client':0, 'server':1}

        results = {'classes':None, 'fields':None, 'methods':None}

        if sender in self.dcc.sockets and self.dcc.sockets[sender]:
            lowlimit  = 0
            highlimit = 100
        else:
            lowlimit  = 1
            highlimit = 10

        self.say(sender, "$B[ SEARCH RESULTS ]")    
        for side in ['client', 'server']:
            c.execute("""SELECT c.name, c.notch FROM vclasses c WHERE (c.name LIKE ?) AND c.side = ? AND c.versionid = ?""",('%%%s%%'%(msg), side_lookup[side], idversion))                   
            results['classes'] = c.fetchall()

            for etype in ['fields', 'methods']:
                c.execute("""SELECT m.name, m.notch, m.searge, m.sig, m.notchsig, m.desc, m.classname, m.classnotch FROM v%s m
                            WHERE (m.name LIKE ? ESCAPE '!') AND m.side = ? AND m.versionid = ?"""%etype, 
                            ('%%%s%%'%(msg), side_lookup[side], idversion))
                results[etype] = c.fetchall()

            if not results['classes']:
                self.say(sender, " [%s][  CLASS] No results"%side.upper())
            else:                
                maxlenname  = max(map(len, [result[0] for result in results['classes']]))
                maxlennotch = max(map(len, [result[1] for result in results['classes']]))
                if len(results['classes']) > highlimit:
                    self.say(sender, " [%s][  CLASS] Too many results : %d"%(side.upper(),len(results['classes'])))
                else:
                    for result in results['classes']:
                        name, notch = result
                        self.say(sender, " [%s][  CLASS] %s %s"%(side.upper(), name.ljust(maxlenname+2), notch.ljust(maxlennotch+2)))            


            for etype in ['fields', 'methods']:
                if not results[etype]:
                    self.say(sender, " [%s][%7s] No results"%(side.upper(), etype.upper()))
                else:
                    maxlenname  = max(map(len, ['%s.%s'%(result[6], result[0])   for result in results[etype]]))
                    maxlennotch = max(map(len, ['[%s.%s]'%(result[7], result[1]) for result in results[etype]]))
                    if len(results[etype]) > highlimit:
                        self.say(sender, " [%s][%7s] Too many results : %d"%(side.upper(),etype.upper(),len(results[etype])))
                    else:
                        for result in results[etype]:
                            name, notch, searge, sig, notchsig, desc, classname, classnotch = result
                            fullname   = '%s.%s'%(classname, name)
                            fullnotch = '[%s.%s]'%(classnotch, notch)
                            self.say(sender, " [%s][%7s] %s %s %s %s"%(side.upper(),etype.upper(), fullname.ljust(maxlenname+2), fullnotch.ljust(maxlennotch+2), sig, notchsig))                
                
    #===================================================================

    #====================== Setters for members ========================
    
    def cmd_scm(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bscm [<id>|<searge>] <newname> [description]$N : Set Client Method."""
        self.setMember(sender, chan, cmd, msg, 'client', 'methods', forced=False)
        
    def cmd_scf(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bscf [<id>|<searge>] <newname> [description]$N : Set Server Method."""
        self.setMember(sender, chan, cmd, msg, 'client', 'fields', forced=False)
        
    def cmd_ssm(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bssm [<id>|<searge>] <newname> [description]$N : Set Client Field."""
        self.setMember(sender, chan, cmd, msg, 'server', 'methods', forced=False)

    def cmd_ssf(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bssf [<id>|<searge>] <newname> [description]$N : Set Server Field."""
        self.setMember(sender, chan, cmd, msg, 'server', 'fields', forced=False)

    def cmd_fscm(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bscm [<id>|<searge>] <newname> [description]$N : Set Client Method."""
        self.setMember(sender, chan, cmd, msg, 'client', 'methods', forced=True)
        
    def cmd_fscf(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bscf [<id>|<searge>] <newname> [description]$N : Set Server Method."""
        self.setMember(sender, chan, cmd, msg, 'client', 'fields', forced=True)
        
    def cmd_fssm(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bssm [<id>|<searge>] <newname> [description]$N : Set Client Field."""
        self.setMember(sender, chan, cmd, msg, 'server', 'methods', forced=True)

    def cmd_fssf(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bssf [<id>|<searge>] <newname> [description]$N : Set Server Field."""
        self.setMember(sender, chan, cmd, msg, 'server', 'fields', forced=True)

    @database
    def setMember(self, sender, chan, cmd, msg, side, etype, *args, **kwargs):
        
        c         = kwargs['cursor']
        idversion = kwargs['idvers']      
        forced    = kwargs['forced']
        
        msg = msg.strip()
        type_lookup = {'methods':'func','fields':'field'}
        side_lookup = {'client':0, 'server':1}
        
        if not msg or msg.split() < 2:
            self.say(sender, "$B[ SET %s %s ]"%(side.upper(),etype.upper()))
            self.say(sender, " Syntax error. Use $B%s <membername> <newname> [newdescription]$N"%(cmd))
            return        
        
        msg     = map(string.strip, msg.split())
        oldname = msg[0]
        newname = msg[1]
        newdesc = None
        if len(msg) > 2:
            newdesc = ' '.join(msg[2:])        

        self.say(sender, "$B[ SET %s %s ]"%(side.upper(),etype.upper()))
        if forced: self.say(sender, "$RCAREFULL, YOU ARE FORCING AN UPDATE !")

        result = c.execute("""SELECT m.name FROM vclasses m WHERE m.name = ? AND m.side = ? AND m.versionid = ?""", (newname, side_lookup[side], idversion)).fetchone()
        if result: 
            self.say(sender, "$RIt is illegal to use class names for fields or methods !")
            return
        
        if not forced:
            result = c.execute("""SELECT m.searge, m.name FROM vmethods m WHERE m.name = ? AND m.side = ? AND m.versionid = ?""", (newname, side_lookup[side], idversion)).fetchone()
            if result: 
                self.say(sender, "$RYou are conflicting with at least one other method: %s. Please use forced update only if you are certain !"%result[0])
                return

            result = c.execute("""SELECT m.searge, m.name FROM vfields m WHERE m.name = ? AND m.side = ? AND m.versionid = ?""", (newname, side_lookup[side], idversion)).fetchone()
            if result: 
                self.say(sender, "$RYou are conflicting with at least one other field: %s. Please use forced update only if you are certain !"%result[0])
                return

        c.execute("""SELECT m.name, m.notch, m.searge, m.sig, m.notchsig, m.desc, m.classname, m.classnotch, m.id FROM v%s m
                    WHERE ((m.searge LIKE ? ESCAPE '!') OR m.searge = ?) AND m.side = ? AND m.versionid = ?"""%etype, 
                    ('%s!_%s!_%%'%(type_lookup[etype],oldname),oldname,side_lookup[side], idversion))            
        
        results = c.fetchall()

        if len(results) > 1:
            self.say(sender, " Ambiguous request $R'%s'$N"%oldname)
            self.say(sender, " Found %s possible answers"%len(rows))
            
            maxlencsv   = max(map(len, ['%s.%s'%(result[5], result[2])   for result in results]))
            maxlennotch = max(map(len, ['[%s.%s]'%(result[6], result[1]) for result in results]))
            for result in results:
                name, notch, searge, sig, notchsig, desc, classname, classnotch, id = result
                fullcsv   = '%s.%s'%(classname, name)
                fullnotch = '[%s.%s]'%(classnotch, notch)
                self.say(sender, " %s %s %s"%(fullcsv.ljust(maxlencsv+2), fullnotch.ljust(maxlennotch+2), sig))
                
        elif len(results) == 0:
            self.say(sender, " No result for %s"%oldname)
        else:
            name, notch, searge, sig, notchsig, desc, classname, classnotch, id = results[0]
            self.say(sender, "Name     : $B%s => %s"%(name, newname))
            self.say(sender, "$BOld desc$N : %s"%(desc))

            if not newdesc:
                self.say(sender, "$BNew desc$N : %s"%(desc))
                c.execute("""INSERT INTO %shist VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""%etype,
                    (None, int(id), name, desc, newname, desc.replace('"',"'"), int(time.time()), sender, forced, cmd))
            elif newdesc == 'None':
                self.say(sender, "$BNew desc$N : None")
                c.execute("""INSERT INTO %shist VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""%etype,
                    (None, int(id), name, desc, newname, None, int(time.time()), sender, forced, cmd))                
            else:
                self.say(sender, "$BNew desc$N : %s"%(newdesc))
                c.execute("""INSERT INTO %shist VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""%etype,
                    (None, int(id), name, desc, newname, newdesc.replace('"',"'"), int(time.time()), sender, forced, cmd))

    #===================================================================

    #====================== Revert changes =============================
    
    @restricted(2)
    def cmd_rcm(self, sender, chan, cmd, msg, *args, **kwargs):
        self.revertChanges(sender, chan, cmd, msg, 'client', 'methods')    

    @restricted(2)   
    def cmd_rcf(self, sender, chan, cmd, msg, *args, **kwargs):
        self.revertChanges(sender, chan, cmd, msg, 'client', 'fields')    
    
    @restricted(2)
    def cmd_rsm(self, sender, chan, cmd, msg, *args, **kwargs):
        self.revertChanges(sender, chan, cmd, msg, 'server', 'methods')
    
    @restricted(2)
    def cmd_rsf(self, sender, chan, cmd, msg, *args, **kwargs):
        self.revertChanges(sender, chan, cmd, msg, 'server', 'fields')
    
    @database
    def revertChanges(self, sender, chan, cmd, msg, side, etype, *args, **kwargs):
        c         = kwargs['cursor']
        idversion = kwargs['idvers']    

        type_lookup = {'methods':'func','fields':'field'}
        side_lookup = {'client':0, 'server':1}
        
        self.say(sender, "$B[ REVERT %s %s ]"%(side.upper(), etype.upper()))
        
        msg = msg.strip()
        if len(msg.split()) > 1:
            self.say(sender, "Syntax error : $B%s <searge|index>"%cmd)
            return
            
    
        c.execute("""UPDATE %s SET dirtyid=0 WHERE ((searge LIKE ? ESCAPE '!') OR searge = ?) AND side = ? AND versionid = ?"""%etype,
         ('%s!_%s!_%%'%(type_lookup[etype],msg),msg,side_lookup[side], idversion))
        self.say(sender, " Reverting changes on $B%s$N is done."%msg)
    
    #===================================================================

    #====================== Log Methods ================================
    @database
    def cmd_getlog(self, sender, chan, cmd, msg, *args, **kwargs):

        c         = kwargs['cursor']
        idversion = kwargs['idvers']    
        
        msg = msg.strip()
        if msg == 'full':fulllog=True
        else: fulllog = False
        
        type_lookup = {'methods':'func','fields':'field'}
        side_lookup = {'client':0, 'server':1}

        self.say(sender, "$B[ LOGS ]")
        for side  in ['server', 'client']:
            for etype in ['methods', 'fields']:
                c.execute("""SELECT m.name, m.searge, m.desc, h.newname, h.newdesc, strftime('%s',h.timestamp, 'unixepoch') as htimestamp, h.nick
                            FROM  %s m 
                            INNER JOIN %shist h ON m.dirtyid = h.id
                            WHERE m.side = ?  AND m.versionid = ? ORDER BY h.timestamp"""%('%m-%d %H:%M',etype,etype), (side_lookup[side], idversion))
                    
                results = c.fetchall()
        
                if results:
                    maxlennick   = max(map(len, [result[6] for result in results]))
                    maxlensearge = max(map(len, [result[1] for result in results]))
                    maxlenmname  = max(map(len, [result[0] for result in results]))

                for result in results:
                    mname, msearge, mdesc, hname, hdesc, htimestamp, hnick = result
                    
                    if fulllog:
                        self.say(sender, "+ %s, %s"%(htimestamp, hnick))
                        self.say(sender, "  [%s%s][%s] %s => %s"%(side[0].upper(), etype[0].upper(), msearge.ljust(maxlensearge), mname.ljust(maxlenmname), hname))
                        self.say(sender, "  [%s%s][%s] %s => %s"%(side[0].upper(), etype[0].upper(), msearge.ljust(maxlensearge), mdesc, hdesc))
                    else:
                        self.say(sender, "+ %s, %s [%s%s] %s => %s"%(htimestamp, hnick.ljust(maxlennick), side[0].upper(), etype[0].upper(), msearge.ljust(maxlensearge), hname))

    @restricted(3)
    def cmd_commit(self, sender, chan, cmd, msg, *args, **kwargs):
        self.dbCommit (sender, chan, cmd, msg)

    @restricted(3)
    def cmd_updatecsv(self, sender, chan, cmd, msg, *args, **kwargs):
        self.dbCommit (sender, chan, cmd, msg)
        self.updateCsv(sender, chan, cmd, msg)
    
    @database
    def updateCsv(self, sender, chan, cmd, msg, *args, **kwargs):

        c         = kwargs['cursor']
        idversion = kwargs['idvers']  
        
        if self.cnick == 'MCPBot_NG':
            directory='.'
        else:
            directory  = '/home/mcpfiles/renamer_csv'
        #directory = "."

        outfieldcsv  = 'fields.csv'
        outmethodcsv = 'methods.csv'        
    
        ffmetho = open('%s/%s'%(directory, outmethodcsv), 'w')
        fffield = open('%s/%s'%(directory, outfieldcsv),  'w')
        
        for i in range(2):
            ffmetho.write('NULL,NULL,NULL,NULL,NULL,NULL\n')
            fffield.write('NULL,NULL,NULL,NULL,NULL,NULL\n')
        fffield.write('Class,Field,Name,Class,Field,Name,Name,Notes\n')
        ffmetho.write('NULL,NULL,NULL,NULL,NULL,NULL\n')
        ffmetho.write('class (for reference only),Reference,class (for reference only),Reference,Name,Notes\n')
        
        c.execute("""SELECT classname, searge, name, desc FROM vfields WHERE side = 0  AND versionid = ? ORDER BY searge""", (idversion,))
        for row in c.fetchall():
            classname, searge, name, desc = row
            if not desc:desc = ''
            fffield.write('%s,*,%s,*,*,*,%s,"%s"\n'%(classname, searge, name, desc.replace('"', "'")))
        c.execute("""SELECT classname, searge, name, desc FROM vfields WHERE side = 1  AND versionid = ? ORDER BY searge""", (idversion,))
        for row in c.fetchall():
            classname, searge, name, desc = row
            if not desc:desc = ''
            fffield.write('*,*,*,%s,*,%s,%s,"%s"\n'%(classname, searge, name, desc.replace('"', "'")))

        c.execute("""SELECT classname, searge, name, desc FROM vmethods WHERE side = 0  AND versionid = ? ORDER BY searge""", (idversion,))
        for row in c.fetchall():
            classname, searge, name, desc = row
            if not desc:desc = ''
            ffmetho.write('%s,%s,*,*,%s,"%s"\n'%(classname, searge, name, desc.replace('"', "'")))
        c.execute("""SELECT classname, searge, name, desc FROM vmethods WHERE side = 1  AND versionid = ? ORDER BY searge""", (idversion,))
        for row in c.fetchall():
            classname, searge, name, desc = row
            if not desc:desc = ''
            ffmetho.write('*,*,%s,%s,%s,"%s"\n'%(classname, searge, name, desc.replace('"', "'")))

        ffmetho.close()
        fffield.close()   
    
    @restricted(5)
    @database
    def cmd_altcsv(self, sender, chan, cmd, msg, *args, **kwargs):
        c         = kwargs['cursor']
        idversion = kwargs['idvers']  

        methodswriter = csv.writer(open('methods.csv', 'wb'), delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
        c.execute("""SELECT searge, name, notch, sig, notchsig, classname, classnotch, package, side FROM vmethods 
                      WHERE NOT name   = classname 
                            AND NOT searge = notch 
                            AND versionid = ?""",(idversion,))
        methodswriter.writerow(('searge', 'name', 'notch', 'sig', 'notchsig', 'classname', 'classnotch', 'package', 'side'))
        for row in c:
            methodswriter.writerow(row)

        fieldswriter = csv.writer(open('fields.csv', 'wb'), delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
        c.execute("""SELECT searge, name, notch, sig, notchsig, classname, classnotch, package, side FROM vfields 
                      WHERE NOT name   = classname 
                            AND NOT searge = notch 
                            AND versionid = ?""",(idversion,))
        fieldswriter.writerow(('searge', 'name', 'notch', 'sig', 'notchsig', 'classname', 'classnotch', 'package', 'side'))
        for row in c:
            fieldswriter.writerow(row)

        classeswriter = csv.writer(open('classes.csv', 'wb'), delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
        c.execute("""SELECT name, notch, supername, package, side FROM vclasses 
                      WHERE NOT name = notch AND versionid = ?""",(idversion,))
        classeswriter.writerow(('name', 'notch', 'supername', 'package', 'side'))
        for row in c:
            classeswriter.writerow(row)

        classeswriter = csv.writer(open('fullclasses.csv', 'wb'), delimiter=',',quotechar='"', quoting=csv.QUOTE_ALL)
        c.execute("""SELECT name, notch, supername, package, side FROM vclasses 
                      WHERE versionid = ?""",(idversion,))
        classeswriter.writerow(('name', 'notch', 'supername', 'package', 'side'))
        for row in c:
            classeswriter.writerow(row)

    @database   
    def dbCommit(self, sender, chan, cmd, msg, *args, **kwargs):

        c         = kwargs['cursor']
        idversion = kwargs['idvers']

        nentries = 0
        for etype in ['methods', 'fields']:

            c.execute("""SELECT m.id, h.id, h.newname, h.newdesc FROM %s m
                        INNER JOIN %shist h ON m.dirtyid = h.id
                        WHERE m.versionid = ?
                        """%(etype, etype), (idversion,))
        
            results = c.fetchall()
            nentries += len(results)
            
            for result in results:
                mid, hid, hnewname, hnewdesc = result
                c.execute("""UPDATE %s SET name = ?, desc = ?, dirtyid = 0 WHERE id = ?"""%etype, (hnewname, hnewdesc, mid))  

        if nentries:
            c.execute("""INSERT INTO commits VALUES (?, ?, ?)""",(None, int(time.time()), sender))
            self.say(sender, "$B[ COMMIT ]")
            self.say(sender, " Committed %d new updates"%nentries)
        else:
            self.say(sender, "$B[ COMMIT ]")
            self.say(sender, " No new entries to commit")    
    
    #===================================================================

    #====================== Whitelist Handling =========================
    @restricted(0)
    def cmd_addwhite(self, sender, chan, cmd, msg, *args, **kwargs):
        msg = msg.strip().split()
        if len(msg) == 1:
            nick  = msg[0]
            level = 4
            if level >= self.whitelist[sender]:
                self.say(sender, "You don't have the rights to do that.")                 
                return
            self.addWhitelist(nick)
        elif len(msg) == 2:
            try:
                nick  = msg[0]
                level = int(msg[1])
                if level > 4:
                    self.say(sender, "Max level is 4.")
                    return
                if level >= self.whitelist[sender]:
                    self.say(sender, "You don't have the rights to do that.")                 
                    return                    
                self.addWhitelist(nick, level)
            except:
                self.say(sender, "Syntax error : $Baddwhite <nick> [level]")
                return
        else:
            self.say(sender, "Syntax error : $Baddwhite <nick> [level]")
        self.say(sender, "Added %s with level %d to whitelist"%(nick, level))
        
    @restricted(0)
    def cmd_rmwhite(self, sender, chan, cmd, msg, *args, **kwargs):
        nick = msg.strip()
        
        if nick in self.whitelist and self.whitelist[nick] >= self.whitelist[sender]:
            self.say(sender, "You don't have the rights to do that.")         
            return
        
        try:
            self.rmWhitelist(nick)
        except KeyError:
            self.say(sender, "User %s not found in the whitelist"%nick)
            return   
        self.say(sender, "User %s removed from the whitelist"%nick)         
    
    @restricted(0)   
    def cmd_getwhite(self, sender, chan, cmd, msg, *args, **kwargs):
        self.say(sender, "Whitelist : %s"%self.whitelist)
        
    @restricted(4)
    def cmd_savewhite(self, sender, chan, cmd, msg, *args, **kwargs):
        self.saveWhitelist()
        
    @restricted(4)
    def cmd_loadwhite(self, sender, chan, cmd, msg, *args, **kwargs):
        self.loadWhitelist()        
    #===================================================================

    #====================== Misc commands ==============================
    @restricted(5)
    def cmd_exec(self, sender, chan, cmd, msg, *args, **kwargs):
        try:
            print msg
            exec(msg) in self.globaldic, self.localdic
        except Exception as errormsg:
            self.printq.put ('ERROR : %s'%errormsg)
            self.say(sender, 'ERROR : %s'%errormsg)

    def cmd_dcc(self, sender, chan, cmd, msg, *args, **kwargs):
        """$Bdcc$N : Starts a dcc session. Faster and not under the flood protection."""        
        self.dcc.dcc(sender)        
    
    @restricted(4)
    def cmd_kick(self, sender, chan, cmd, msg, *args, **kwargs):
        msg = msg.strip()
        msg = msg.split()
        if not len(msg) >= 2:return
        if len(msg) == 2:
            self.irc.kick(msg[0], msg[1])
        if len(msg) > 2:
            self.irc.kick(msg[0], msg[1], ' '.join(msg[2:]))

    @restricted(5)
    def cmd_rawcmd(self, sender, chan, cmd, msg, *args, **kwargs):
        self.irc.rawcmd(msg.strip())

    def cmd_help(self, sender, chan, cmd, msg, *args, **kwargs):
        self.say(sender, "$B[ HELP ]")
        self.say(sender, "For help, please check : http://mcp.ocean-labs.de/index.php/MCPBot")

    @database
    def cmd_status(self, sender, chan, cmd, msg, *args, **kwargs):
        c         = kwargs['cursor']
        idversion = kwargs['idvers']

        type_lookup = {'methods':'func','fields':'field'}
        side_lookup = {'client':0, 'server':1}

        
        mcpversion, botversion, dbversion, clientversion, serverversion = \
            c.execute ("""SELECT mcpversion, botversion, dbversion, clientversion, serverversion FROM versions WHERE id = ?""", (idversion,)).fetchone()
            
        self.say(sender, "$B[ STATUS ]")
        self.say(sender, " MCP    : $B%s"%mcpversion)
        self.say(sender, " Bot    : $B%s"%botversion)
        self.say(sender, " Client : $B%s"%clientversion)
        self.say(sender, " Server : $B%s"%serverversion)

        for side  in ['client', 'server']:
            for etype in ['methods', 'fields']:
                total, ren, urn = c.execute("""SELECT total(%st), total(%sr), total(%su) 
                                      FROM vclassesstats WHERE side = ? AND versionid = ?"""%(etype,etype,etype), 
                                      (side_lookup[side], idversion)).fetchone()
                                      
                self.say(sender, " [%s][%7s] : T $B%4d$N | R $B%4d$N | U $B%4d$N | $B%5.2f%%$N" %(side[0].upper(), etype.upper(), total, ren, urn, float(ren)/float(total)*100))
                
        nthreads = len(threading.enumerate())
        if nthreads == self.nthreads + 1:
            self.say(sender, " All threads up and running !")
        else:
            self.say(sender, " Found only $R%d$N threads ! $BThere is a problem !"%(nthreads-1))

    @restricted(4)
    def cmd_listthreads(self, sender, chan, cmd, msg, *args, **kwargs):
        threads = threading.enumerate()
        threads.pop(0)
        self.say(sender, "$B[ THREADS ]")
        threads = sorted(threads, cmp=lambda a,b:cmp(a.ncalls,b.ncalls))
        maxthreadname = max([len(i.name) for i in threads])
        
        displayorder = zip(range(0,len(threads),2), range(1,len(threads),2))
        
        for i,j in displayorder:
            it = threads[i]
            jt = threads[j]
            self.say(sender, '%2d %s %4d %4d %4d | %2d %s %4d %4d %4d'%
            (i, it.name.ljust(maxthreadname), it.ncalls, it.nscalls, it.nfcalls,
             j, jt.name.ljust(maxthreadname), jt.ncalls, jt.nscalls, jt.nfcalls))
        
        if len(threads)%2 == 1:
            i = threads[-1]
            self.say(sender, '%2d %s %4d %4d %4d'%(len(threads)-1, i.name.ljust(maxthreadname), i.ncalls, i.nscalls, i.nfcalls))

    @restricted(4)
    def cmd_listdcc(self, sender, chan, cmd, msg, *args, **kwargs):
        self.say(sender, str(self.dcc.sockets.keys()))

    @database
    def cmd_todo(self, sender, chan, cmd, msg, *args, **kwargs):
        c         = kwargs['cursor']
        idversion = kwargs['idvers']

        type_lookup = {'methods':'func','fields':'field'}
        side_lookup = {'client':0, 'server':1}
        
        if not msg in ['client', 'server']:
            self.say(sender, "$Btodo <client|server>")
            return

        results = c.execute("""SELECT id, name, methodst + fieldst, methodsr  + fieldsr, methodsu  + fieldsu
                                FROM vclassesstats WHERE side = ? AND versionid = ? ORDER BY methodsu + fieldsu DESC LIMIT 10""",
                                (side_lookup[msg], idversion)).fetchall()

        self.say(sender, "$B[ TODO %s ]"%msg.upper())
        for result in results:
            id, name, memberst, membersr, membersu = result
            if not memberst: memberst = 0
            if not membersr: membersr = 0
            if not membersu: membersu = 0
            if membersr == 0: percent = 0.
            else: percent = float(membersr)/float(memberst)*100.0
            self.say(sender, " %s : $B%2d$N [ T $B%3d$N | R $B%3d$N | $B%5.2f%%$N ] "%(name.ljust(20), membersu, memberst, membersr, percent))

#==END OF CLASS==


