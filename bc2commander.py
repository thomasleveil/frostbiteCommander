#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Provide a text console for BFBC2 servers with command help and autocompletion
# 
# CHANGELOG : 
# v1.0 :
#   * fix bug when password is provided on the command line
#   * cmd doc is now complete and updated from http://blogs.battlefield.ea.com/battlefield_bad_company/archive/2010/02/05/remote-administration-interface-for-bfbc2-pc.aspx## R7
#   * on Windows, wait for the user to press the Enter key before exiting
# v1.1
#   * add missing imp import (do not affect Windows dist)
# v2.0
#   * display the cmd help in case of non 'OK' response from the BFBC2 server
#   * login.hashed asks the user for its passwords, computes and sends the hash automatically
#   * allow to define custom behaviour for bfbc2 commands by defining function named after
#       the pattern : bfbc2_<cmdBeforeDot>_<cmdAfterDot>
#       ie: login.hashed -> bfbc2_login_hashed
# v3.0
#   * fix bfbc2_logout
#   * make the command document easier to read
#   * display words sent to the BFBC2 server
#   * provide arguments completion for commands expecting a boolean
#   * refactor to make Bfbc2Commander_* class writting more conventional (regaring the cmd.Cmd documentation)
# v3.1
#   * add R9 commands documentation
#   * improve R8 commands documentation formatting
# v3.2
#   * displays command help if the return value is not 'OK' and not 'UnknownCommand'
#   * add parameters completion for admin.listPlayers
# v3.3 
#   * fix command completion for admin.listPlayers
#   * add command completion for :
#        admin.getPlaylist
#        admin.setPlaylist
#        admin.kickPlayer
#        admin.banPlayer
#        admin.unbanPlayer
#        reservedSlots.addPlayer
#        reservedSlots.removePlayer
# v3.4
#  * update documentation for admin.say for R9 server
# v3.5
#  * update CommandConsole with R9 file from DICE examples
#  * update R9 documentation
# v3.6 
#  * add cmd doc for admin.killPlayer, admin.movePlayer, admin.shutdown
#  * remove R8 support
#  * add hidden help topic "_undocumented_commands"
#
__author__ = "Thomas Leveil <thomasleveil@gmail.com>"
__version__ = "3.6"


import sys
import string
import re
import cmd
import socket
import imp
import time
import readline
import getpass
from CommandConsole import *



class Bfbc2Commander(cmd.Cmd):
    """BFBC2 command processor"""
    identchars = cmd.IDENTCHARS + '.'
    _socket = None
    _receiveBuffer = ''
    _bfbc2cmdList = []
    _bfbc2UnprivilegedCmdList = ['login.hashed', 'login.plainText', 'logout', 'quit', 'serverInfo', 'version']
    _connectedPlayersCache = []
    _connectedPlayersCacheTime = None
    _playlistsCache = None
    _bannedPlayersCache = []
    _bannedPlayersCacheTime = None
    _reservedSlotsCache = []
    _reservedSlotsCacheTime = None
    
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = '> '
        
    def initSocket(self, socket, receiveBuffer=''):
        self._socket = socket
        self._receiveBuffer = receiveBuffer
        self._initAvailableCmds()
        
    def _initAvailableCmds(self):
        """depending on the login status, build up the list of available commands"""
        words = self._sendBfbc2Cmd('help', verbose=False)
        if words[0] == 'OK':
            self._bfbc2cmdList = words[1:]
        else:
            self._bfbc2cmdList = self._bfbc2UnprivilegedCmdList
        
    def _sendBfbc2Cmd(self, command, verbose=True):
        """send a command through the BFBC2 socket and returns the response's words"""
        words = shlex.split(command)

        if len(words) >= 1:

            if "quit" == words[0]:
                sys.exit(0)

            # Send request to server on command channel
            request = EncodeClientRequest(words)
            if verbose: print words
            self._socket.send(request)

            # Wait for response from server
            [packet, self._receiveBuffer] = receivePacket(self._socket, self._receiveBuffer)

            [isFromServer, isResponse, sequence, words] = DecodePacket(packet)

            # The packet from the server should 
            # For now, we always respond with an "OK"
            if not isResponse:
                if verbose: print 'Received an unexpected request packet from server, ignored: %s' % (DecodePacket(packet),)

            #printPacket(DecodePacket(packet))
            return words
    
    def _getConnectedPlayers(self):
        if self._connectedPlayersCacheTime is not None \
            and (time.clock() - self._connectedPlayersCacheTime) < 3:
            return self._connectedPlayersCache
        else:
            words = self._sendBfbc2Cmd('admin.listPlayers all', verbose=False)
            if words[0] == 'OK':
                self._connectedPlayersCache = [] 
                data = words[1:]
                idx = 1
                while idx < len(data):
                    name = '"' + data[idx] + '"'
                    self._connectedPlayersCache.append(name)
                    idx += 4
                self._connectedPlayersCacheTime = time.clock()
                return self._connectedPlayersCache
            else:
                return []
            
    def _getBannedPlayers(self):
        if self._bannedPlayersCacheTime is not None \
            and (time.clock() - self._bannedPlayersCacheTime) < 3:
            return self._bannedPlayersCache
        else:
            words = self._sendBfbc2Cmd('admin.listPlayerBans', verbose=False)
            if words[0] == 'OK':
                self._bannedPlayersCache = [] 
                regBannedPlayers = re.compile('(\["(?P<name>[^"]+)"]\s+=\s+{[^}]+},\s*)')
                for i in regBannedPlayers.finditer(words[1]):
                    name = i.group('name')
                    self._bannedPlayersCache.append(name)
                self._bannedPlayersCacheTime = time.clock()
                return self._bannedPlayersCache
            else:
                return []
            
    def _getReservedSlots(self):
        if self._reservedSlotsCacheTime is not None \
            and (time.clock() - self._reservedSlotsCacheTime) < 2:
            return self._reservedSlotsCache
        else:
            words = self._sendBfbc2Cmd('reservedSlots.list', verbose=False)
            if words[0] == 'OK':
                self._reservedSlotsCache = words[1:]
                self._reservedSlotsCacheTime = time.clock()
                return self._reservedSlotsCache
            else:
                return []
            
    def _getPlaylists(self):
        if self._playlistsCache is not None:
            return self._playlistsCache
        else:
            words = self._sendBfbc2Cmd('admin.getPlaylists', verbose=False)
            if words[0] == 'OK':
                self._playlistsCache = words[1:]
                return self._playlistsCache
            else:
                return []
    
    def parseline(self, line):
        """Parse the line into a command name and a string containing
        the arguments.  Returns a tuple containing (command, args, line).
        'command' and 'args' may be None if the line couldn't be parsed.
        Dots in 'command' are replaced by '_'
        """
        command, arg, line = cmd.Cmd.parseline(self, line)
        if command:
            command = command.replace('.', '_')
        return command, arg, line
    
    def postcmd(self, words, line):
        """Hook method executed just after a command dispatch is finished.
        If the 1st word received from the command is not 'OK', try to display
        the command help
        """
        cmd, arg, line = self.parseline(line)
        if words and words[0] != 'OK' and words[0] != 'UnknownCommand':
            self.do_help(cmd)
            
    def emptyline(self):
        pass

    def default(self, line):
        """what to do if no do_<cmd> an no bfbc2_<cmd> function are found"""
        words = self._sendBfbc2Cmd(line)
        print words
        return words
    
    def completenames(self, text, *ignored):
        """command names completion. return a list of matching commands"""
        cmds = self._bfbc2cmdList
        if 'help' not in cmds:
            cmds.insert(0, 'help')

        return [a for a in cmds if a.lower().startswith(text.lower())]

    def do_help(self, line):
        """override default help command"""
        command, arg, line = self.parseline(line)
        if command:
            cmd.Cmd.do_help(self, command)
        else:
            print "Available commands :"
            print "====================\n"
            self.columnize(self._bfbc2cmdList)
        
    def do_EOF(self, arg):
        raise SystemExit
        
        
    def do_login_plainText(self, arg):
        words = self._sendBfbc2Cmd('login.plainText ' + arg)
        print words
        self._initAvailableCmds()
        return words

    def do_logout(self, arg):
        words = self._sendBfbc2Cmd('logout ' + arg)
        print words
        self._initAvailableCmds()
        return words
        
    def do_login_hashed(self, arg):
        if arg and len(arg.strip())>0:
            words = self._sendBfbc2Cmd('login.hashed ' + arg)
            print words
            return words
        else:
            """ hashed authentication helper """
            words = self._sendBfbc2Cmd('login.hashed')
            print words
            if words[0]=='OK':
                salt = words[1].decode("hex")
                pw = getpass.getpass()
                passwordHash = generatePasswordHash(salt, pw)
                passwordHashHexString = string.upper(passwordHash.encode("hex"))
                print "login.hashed " + passwordHashHexString
                words = self._sendBfbc2Cmd("login.hashed " + passwordHashHexString)
                print words
                self._initAvailableCmds()
                return words
    
    def get_undocumented_commands(self):
        undoc_cmds = []
        for bfbc2cmd in self._bfbc2cmdList:
            command, arg, line = self.parseline(bfbc2cmd)
            if not hasattr(self, 'help_' + command):
                undoc_cmds.append(bfbc2cmd)
        return undoc_cmds

    def help__undocumented_commands(self):
        print "Undocumented commands :"
        print "=======================\n"
        self.columnize(self.get_undocumented_commands())


    
class Bfbc2Commander_R9(Bfbc2Commander):
    _bfbc2UnprivilegedCmdList = ['login.hashed', 'login.plainText', 'logout', 'quit', 'serverInfo', 'listPlayers', 'version']
    
    def _complete_boolean(self, text, line, begidx, endidx):
        #print "\n>%s\t%s[%s:%s] = %s" % (text, line, begidx, endidx, line[begidx:endidx])
        completions = ['true', 'false']
        return [a for a in completions if a.startswith(line[begidx:endidx])]
    
    
    def help_login_plainText(self):
        print """
 Request: login.plainText <password: string> 

Response: OK - Login successful, you are now logged in regardless of prior 
          status 
Response: InvalidPassword - Login unsuccessful, logged-in status unchanged 
Response: PasswordNotSet  - Login unsuccessful, logged-in status unchanged 
Response: InvalidArguments

  Effect: Attempt to login to game server with password <password> 
Comments: If you are connecting to the admin interface over the internet, then 
          use login.hashed instead to avoid having evildoers sniff the admin 
          password
"""

    def help_login_hashed(self):
        print """
 Request: login.hashed 
 
Response: OK <salt: HexString> - Retrieved salt for the current connection 
Response: PasswordNotSet - No password set for server, login impossible 
Response: InvalidArguments 
  Effect: Retrieves the salt, used in the hashed 
          password login process 

Comments: This is step 1 in the 2-step hashed password process. When using this 
          people cannot sniff your admin password.


 Request: login.hashed <passwordHash: HexString> 
 
Response: OK - Login successful, you are now logged in regardless of prior 
          status 
Response: PasswordNotSet - No password set for server, login impossible 
Response: InvalidPasswordHash - Login unsuccessful, logged-in status unchanged 
Response: InvalidArguments 
  Effect: Sends a hashed password to the server, in an 
          attempt to log in 
          
Comments: This is step 2 in the 2-step hashed password process. When using this 
        people cannot sniff your admin password.
"""

    def help_logout(self):
        print """
 Request: logout 
 
Response: OK - You are now logged out regardless of prior status 
Response: InvalidArguments 

  Effect: Logout from game server
"""

    def help_quit(self): 
        print """
 Request: quit 
 
Response: OK 
Response: InvalidArguments 

  Effect: Disconnect from server
"""

    def help_version(self):
        print """
 Request: version 
 
Response: OK BFBC2 <version> 
Response: InvalidArguments 

  Effect: Reports game server type, and build ID 
Comments: Game server type and build ID uniquely identify the server, and the 
          protocol it is running.
"""
   
    def help_listPlayers(self):
        print """\
 Request: listPlayers <players: player subset>
  
Response: OK <player info> 
Response: InvalidArguments
 
  Effect: Return list of all players on the server, but with zeroed out GUIDs
"""

    def help_eventsEnabled(self): 
        print """
 Request: eventsEnabled [enabled: boolean] 
 
Response: OK - for set operation 
Response: OK <enabled: boolean> - for get operation 
Response: InvalidArguments 

  Effect: Set whether or not the server will send events to the current 
          connection
"""
    complete_eventsEnabled = _complete_boolean

    def help_help(self):
        print """
 Request: help 
 
Response: OK <all commands available on server, as separate words> 
Response: InvalidArguments 

  Effect: Report which commands the server knows about
"""

    def help_admin_runScript(self):
        print """
 Request: admin.runScript <filename: filename> 
 
Response: OK 
Response: InvalidArguments 
Response: InvalidFileName - The filename specified does not follow filename 
          rules 
Response: ScriptError <line> <original error...> - Script failed at line <line>, 
          with the given error 

  Effect: Process file, executing script lines one-by-one, aborting processing 
          upon error
"""

    def help_punkBuster_pb_sv_command(self):
        print """
 Request: punkBuster.pb_sv_command <command: string> 
 
Response: OK - Command sent to PunkBuster server module 
Response: InvalidArguments 
Response: InvalidPbServerCommand - Command does not begin with 'pb_sv_'

  Effect: Send a raw PunkBuster command to the PunkBuster server 
 Comment: The entire command is to be sent as a single string. Don't split it 
          into multiple words.
"""

    def help_serverInfo(self):
        print """
 Request: serverInfo 
 
Response: OK <serverName> <current playercount> <max playercount> <current gamem
			ode> <current map> <current round> <max rounds> 
Response: InvalidArguments 

  Effect: Query for brief server info. 
Comments: This command can be performed without being logged in.
"""

    def help_admin_yell(self):
        print """
 Request: admin.yell <message: string> <duration [in ms]: integer> 
                                                        <players: player subset>
Response: OK
Response: InvalidArguments
Response: TooLongMessage
Response: InvalidDuration

  Effect: Display a message, very visibly on players' screens, for a certain 
          amount of time. The duration must be more than 0 and at most 60000 ms.
          The message must be less than 100 characters long.
"""

    def help_admin_say(self):
        print """
 Request: admin.say <message: string> <players: player subset>
 
Response: OK
Response: InvalidArguments
Response: TooLongMessage

  Effect: Send a chat message to players. The message must be less 
          than 100 characters long.
"""

    def help_admin_runNextLevel(self):
        print """
 Request: admin.runNextLevel
 
Response: OK
Response: InvalidArguments

  Effect: Switch to next level
Comments: Always successful.
"""

    def help_admin_currentLevel(self):
        print """
 Request: admin.currentLevel
 
Response: OK <name>
Response: InvalidArguments

  Effect: Return current level name
"""

    def help_mapList_nextLevelIndex(self):
        print """\
 Request:  mapList.nextLevelIndex  
Response:  OK  
  Effect:  Get index of next level to be run 
 
 
 Request:  mapList.nextLevelIndex <index: integer>  
  
Response:  OK  
Response:  InvalidArguments  
Response:  InvalidIndex  - Level index not available in server map list  

  Effect:  Set index of next level to be run to <index>  
"""

    def help_admin_restartMap(self):
        print """
 Request: admin.restartMap
 
Response: OK
Response: InvalidArguments
Response: LevelNotAvailable - server currently has no level loaded / level not 
          available on server

  Effect: End current round, and restart with the same map
"""

    def help_admin_supportedMaps(self):
        print """
 Request: admin.supportedMaps <play list: string>
 
Response: OK <map names>
Response: InvalidArguments
Response: InvalidPlaylist <play list> - Play list doesn't exist. 

  Effect: Retrieve maplist of maps supported in this play list
"""

    def help_admin_setPlaylist(self):
        print """
 Request: admin.setPlaylist <name: string>
 
Response: OK - Play list was changed
Response: InvalidArguments
Response: InvalidPlaylist - Play list doesn't exist on server. Should be RUSH, 
		  CONQUEST, SQDM or SQRUSH.

  Effect: Set the play list on the server.
Comments: Will only use maps supported for this play list. So the mapList might 
          be invalid 
   Delay: Change occurs after end of round
"""

    def help_admin_getPlaylist(self):
        print """
 Request: admin.getPlaylist
 
Response: OK <play list>
Response: InvalidArguments

  Effect: Get the current play list for the server
"""

    def help_admin_getPlaylists(self):
        print """
 Request: admin.getPlaylists
 
Response: OK <play lists>
Response: InvalidArguments

  Effect: Get the play lists for the server
"""

    def help_admin_kickPlayer(self):
        print """
 Request:  admin.kickPlayer  <soldier name: player name, reason: string>
 
Response:  OK - Player did exist, and got kicked  
Response:  InvalidArguments  
Response:  PlayerNotFound  - Player name doesn't exist on server 
  
  Effect:  Kick player <soldier name> from server  
Comments:  Reason text is optional. Default reason is 'Kicked by administrator'.  
"""

    def help_admin_killPlayer(self):
        print """
 Request:  admin.killPlayer  <soldier name: player name>
 
Response:  OK - Player did exist, and kill him 
Response:  InvalidArguments  
Response:  InvalidPlayerName  - Player name doesn't exist on server 
  
  Effect:  Kill player <soldier name>
"""

    def help_admin_listPlayers(self):
        print """
 Request: admin.listPlayers <players: player subset>
 
Response: OK <player info> 
Response: InvalidArguments

  Effect: Return list of all players on the server
"""

    def help_admin_movePlayer(self):
        print """
 Request:  admin.movePlayer  <soldier name: player name> <team: teamID> <squad: squadID> <bool: forceKill>
 
Response:  OK
Response:  InvalidArguments  
Response:  InvalidPlayerName  - Player name doesn't exist on server 
Response:  InvalidForceKill  - forceKill must be 'true' or 'false' 
  
  Effect:  move player to teamID, squadID after he dies. If forceKill is
           true, then also kill him
"""

    def help_admin_shutDown(self):
        print """
 Request:  admin.shutDown
 
Response:  OK
Response:  InvalidArguments  
  
  Effect:  shutdown the server
"""


    def help_banList_load(self):
        print """\
 Request: banList.load 

Response: OK 
Response: InvalidArguments 
Response: InvalidIdType 
Response: InvalidBanType 
Response: InvalidTimeStamp - A time stamp could not be read 
Response: IncompleteBan - Incomplete ban entry at end of file 
Response: AccessError - Could not read from file 

  Effect: Load list of banned players/IPs/GUIDs from file 
 Comment: 5 lines (Id-type, id, ban-type, time and reason) are retrieved for 
          every ban in the list. Entries read before getting InvalidIdType, 
          InvalidBanType, InvalidTimeStamp and IncompleteBan is still loaded.
"""

    def help_banList_save(self):
        print """\
 Request: banList.save 

Response: OK 
Response: InvalidArguments 
Response: AccessError - Could not save to file 

  Effect: Save list of banned players/IPs/GUIDs to file 
 Comment: 5 lines (Id-type, id, ban-type, time and reason) are stored for every
          ban in the list. Every line break has windows '\r\n' characters.
"""

    def help_banList_add(self):
        print """\
 Request: banList.add <id-type: id-type> <id: string> <timeout: timeout> 
                                                               <reason: string> 
Response: OK 
Response: InvalidArguments 
Response: BanListFull 

  Effect: Add player to ban list for a certain amount of time 
Comments: Adding a new player/IP/GUID ban will replace any previous ban for that
          player/IP/GUID 
          Timeout can take three forms: 
              perm - permanent [default] 
              round - until end of round 
              seconds <integer> - number of seconds until ban expires 
          Id-type can be any of these :
              name - A soldier name 
              ip - An IP address 
              guid - A player guid
          Id could be either a soldier name, ip address or guid depending on 
          id-type. Reason is optional and defaults to 'Banned by admin'; max 
          length 80 chars. The ban list can contain at most 100 entries.
"""

    def help_banList_remove(self):
        print """\
 Request: banList.remove <id-type: id-type> <id: string> 

Response: OK 
Response: InvalidArguments 
Response: NotFound - Id not found in banlist; banlist unchanged 

  Effect: Remove player/ip/guid from banlist
"""

    def help_banList_clear(self):
        print """\
 Request: banList.clear 

Response: OK 
Response: InvalidArguments 

Effect: Clears ban list
"""

    def help_banList_list(self):
        print """\
 Request: banList.list 
 
Response: OK <player ban entries> 
Response: InvalidArguments 

  Effect: Return list of banned players/IPs/GUIDs. 
 Comment: The list starts with a number telling how many bans the list is 
          holding. After that, 5 words (Id-type, id, ban-type, time and reason)
          are received for every ban in the list.
"""

    def help_reservedSlots_configFile(self):
        print """
 Request: reservedSlots.configFile [filename: filename] - disabled for security
          reasons atm
          
Response: OK - for set option
Response: OK <filename> - for get option
Response: InvalidArguments
Response: InvalidFileName - Filename does not follow filename rules

  Effect: Set name of reserved slots configuration file
"""

    def help_reservedSlots_load(self):
        print """
 Request: reservedSlots.load
 
Response: OK
Response: InvalidArguments
Response: AccessError - File not found; internal reserved slots list is now 
          empty
          
  Effect: Load list of soldier names from file. This is a file with one soldier
          name per line. If loading succeeds, the reserved slots list will get 
          updated. If loading fails, the reserved slots list will remain 
          unchanged.
"""

    def help_reservedSlots_save(self):
        print """
 Request: reservedSlots.save
 
Response: OK
Response: InvalidArguments
Response: AccessError - Error while saving

  Effect: Save list of reserved soldier names to file. This is a file with one 
          soldier name per line.
Comment: If saving fails, the output file may be unchanged or corrupt.
"""

    def help_reservedSlots_addPlayer(self):
        print """
 Request: reservedSlots.addPlayer <soldier name: player name>
 
Response: OK
Response: InvalidArguments
Response: PlayerAlreadyInList - Player is already in the list; reserved slots 
          list unchanged
          
  Effect: Add <soldier name> to list of players who can use the reserved slots.
"""

    def help_reservedSlots_removePlayer(self):
        print """
 Request: reservedSlots.removePlayer <soldier name: player name>
 
Response: OK
Response: InvalidArguments
Response: PlayerNotInList - Player does not exist in list; reserved slots list 
          unchanged
          
  Effect: Remove <soldier name> from list of players who can use the reserved 
          slots.
"""

    def help_reservedSlots_clear(self):
        print """
 Request: reservedSlots.clear
 
Response: OK
Response: InvalidArguments

  Effect: Clear reserved slots list
"""

    def help_reservedSlots_list(self):
        print """
 Request: reservedSlots.list
 
Response: OK <soldier names>
Response: InvalidArguments

  Effect: Retrieve list of players who can utilize the reserved slots
"""

    def help_mapList_configFile(self):
        print """
 Request: mapList.configFile [filename: filename] - disabled for security 
          reasons atm
          
Response: OK - for set option
Response: OK <filename> - for get option
Response: InvalidArguments
Response: InvalidFileName - Filename does not follow filename rules

  Effect: Set name of maplist configuration file
"""

    def help_mapList_load(self):
        print """
 Request: mapList.load
 
Response: OK - Maplist loaded
Response: InvalidArguments
Response: AccessError - File not found, internal maplist is now empty
Response: InvalidPlaylist - Play list doesn't exist. Should be RUSH, CONQUEST, 
          SQDM or SQRUSH.
Response: InvalidMapName <name> - Map with name <name> doesn't exist in 
          playlist/gamemode

  Effect: Load list of map names from file. This is a file with one map name 
          per line.
Comments: If loading succeeds, the maplist will get updated. 
          If loading fails, the maplist will remain unchanged.
"""

    def help_mapList_save(self):
        print """
 Request: mapList.save
 
Response: OK - Maplist saved
Response: InvalidArguments
Response: AccessError - Error while saving, on-disk maplist file possibly 
          corrupted now
          
  Effect: Save maplist to file. This is a file with one map name per line.
Comments: If saving fails, the output file may be unchanged or corrupt.
          Every line break has windows '\r\n' characters.
"""

    def help_mapList_list(self):
        print """
 Request: mapList.list
 
Response: OK <map names>
Response: InvalidArguments

  Effect: Retrieve current maplist
"""

    def help_mapList_clear(self):
        print """
 Request: mapList.clear
 
Response: OK
Response: InvalidArguments

  Effect: Clears maplist
Comments: If server attempts to switch level while maplist is cleared, nasty 
          things will happen
"""

    def help_mapList_remove(self):
        print """
 Request: mapList.remove <index: integer> 
 
Response: OK - Map removed from list 
Response: InvalidArguments 
Response: InvalidIndex - Index doesn't exist in server map list 

  Effect: Remove map from list.
"""

    def help_mapList_append(self):
        print """
 Request: mapList.append <name: string> 

Response: OK - Map appended to list 
Response: InvalidArguments 
Response: InvalidMapName - Map doesn't exist on server 

  Effect: Add map with name <name> to end of maplist 
 Comment: Remember to specify playlist before adding maps
"""

    def help_mapList_insert(self):
        print """\
 Request: mapList.insert <index: integer, name: string> 

Response: OK - Map inserted to list 
Response: InvalidArguments 
Response: InvalidMapName - Map doesn't exist on server or negative index 

  Effect: Add map with name at the specified index to the maplist
"""
        
    def help_vars_adminPassword(self):
        print """
 Request: vars.adminPassword [password: password]
 
Response: OK - for set operation
Response: OK <password> - for get operation
Response: InvalidArguments
Response: InvalidPassword - password does not conform to password format rules

  Effect: Set the admin password for the server, use it with an empty string("") to reset
"""

    def help_vars_gamePassword(self):
        print """
 Request: vars.gamePassword [password: password]
 
Response: OK - for set operation
Response: OK <password> - for get operation
Response: InvalidArguments
Response: InvalidPassword - password does not conform to password format rules
Response: InvalidConfig - password can't be set if ranked is enabled

  Effect: Set the game password for the server, use it with an empty string("")
          to reset
"""

    def help_vars_punkBuster(self):
        print """
 Request: vars.punkBuster [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Response: InvalidConfig - punkbuster can't be disabled if ranked is enabled 
Response: StartupOnlyCallNotAllowed - this command can only be executed from 
          startup.txt

  Effect: Set if the server will use PunkBuster or not
"""
    complete_vars_punkBuster = _complete_boolean
    
    def help_vars_hardCore(self):
        print """
 Request: vars.hardCore [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments

  Effect: Set hardcore mode 
   Delay: Works after map change
"""
    complete_vars_hardCore = _complete_boolean

    def help_vars_ranked(self):
        print """
 Request: vars.ranked [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation 
Response: InvalidArguments
Response: StartupOnlyCallNotAllowed - this command can only be executed from 
          startup.txt 

  Effect: Set ranked or not. If enabled: game password will be removed and 
          punkbuster enabled
"""
    complete_vars_ranked = _complete_boolean

    def help_vars_rankLimit(self):
        print """
 Request: vars.rankLimit <rank: integer> ##QA: Says 'OK' but still allow higher
          ranked players to join
          
Response: OK - for set operation
Response: OK <rank: integer> - for get operation
Response: InvalidArguments

  Effect: Set the highest rank allowed on to the server (integer value).
 Comment: To disable rank limit use -1 as value
"""

    def help_vars_teamBalance(self):
        print """
 Request: vars.teamBalance [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments

  Effect: Set if the server should autobalance
"""
    complete_vars_teamBalance = _complete_boolean

    def help_vars_friendlyFire(self):
        print """
 Request: vars.friendlyFire [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Response: LevelNotLoaded  - for set operation

  Effect: Set if the server should allow team damage 
   Delay: Works after round restart 
 Comment: Not available during level load.
"""

    def help_vars_currentPlayerLimit(self):
        print """
 Request: vars.currentPlayerLimit
 
Response: OK <nr of players: integer> - for get operation
Response: ReadOnly - if you try to send any arguments
Response: InvalidArguments

  Effect: Retrieve the current maximum number of players
 Comment: This value is computed from all the different player limits in effect 
         at any given moment
"""

    def help_vars_maxPlayerLimit(self):
        print """
 Request: vars.maxPlayerLimit
 
Response: OK <nr of players: integer> - for get operation
Response: ReadOnly - if you try to send any arguments
Response: InvalidArguments

  Effect: Retrieve the server-enforced maximum number of players
 Comment: Setting the user-defined maximum number of players higher than this 
          has no effect
"""

    def help_vars_playerLimit(self):
        print """
 Request: vars.playerLimit [nr of players: integer]
 
Response: OK - for set operation
Response: OK <nr of players: integer> - for get operation
Response: InvalidArguments
Response: InvalidNrOfPlayers - Player limit must be in the range 8..32

  Effect: Set desired maximum number of players
 Comment: The effective maximum number of players is also effected by the server
          provider, and the game engine
"""

    def help_vars_bannerUrl(self):
        print """
 Request: vars.bannerUrl [url: string]
 
Response: OK - for set operation
Response: OK <url: string> - for get operation
Response: InvalidArguments
Response: TooLongUrl - for set operation

  Effect: Set banner url
 Comment: The banner url needs to be less than 64 characters long The banner 
          needs to be a 512x64 picture smaller than 127kb 
 Example: admin.setBannerUrl http://www.example.com/banner.jpg
"""

    def help_vars_serverDescription(self):
        print """
 Request: vars.serverDescription <description: string>
 
Response: OK - for set operation
Response: OK <description: string> - for get operation
Response: InvalidArguments
Response: TooLongDescription - for set operation

  Effect: Set server description
 Comment: The description needs to be less than 400 characters long
"""

    def help_vars_killCam(self):
        print """
 Request: vars.killCam [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments

  Effect: Set if killcam is enabled 
   Delay: Works after map switch
"""
    complete_vars_killCam = _complete_boolean

    def help_vars_miniMap(self):
        print """
 Request: vars.miniMap [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments

  Effect: Set if minimap is enabled 
   Delay: Works after map switch
"""
    complete_vars_miniMap = _complete_boolean

    def help_vars_crossHair(self):
        print """
 Request: vars.crossHair [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments

  Effect: Set if crosshair for all weapons is enabled 
   Delay: Works after map 
          switch
"""
    complete_vars_crossHair = _complete_boolean

    def help_vars_3dSpotting(self):
        print """
 Request: vars.3dSpotting [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments

  Effect: Set if spotted targets are visible in the 3d-world 
   Delay: Works after
          map switch
"""
    complete_vars_3dSpotting = _complete_boolean

    def help_vars_miniMapSpotting(self):
        print """
 Request: vars.miniMapSpotting [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments

  Effect: Set if spotted targets are visible on the minimap 
   Delay: Works after 
          map switch
"""
    complete_vars_miniMapSpotting = _complete_boolean

    def help_vars_thirdPersonVehicleCameras(self):
        print """
 Request: vars.thirdPersonVehicleCameras [enabled: boolean]
 
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments

  Effect: <todo> 
   Delay: Works after map switch
##QA: Works but is bugged. If you change the setting and someone is in a vehicle in 3rd person view when at end of round, that player will be stuck in 3rd person view even though the setting should only allow 1st person view.
"""
    complete_vars_thirdPersonVehicleCameras = _complete_boolean







def main_is_frozen():
    """detect if the script is running from frozen
    distribution. i.e: from a py2exe build or others
    """
    return (hasattr(sys, "frozen") or # new py2exe
        hasattr(sys, "importers") or # old py2exe
        imp.is_frozen("__main__")) # tools/freeze

        
def main():
    from getopt import getopt

    print "BFBC2 Commander"
    serverSocket = None

    host = None
    port = None
    pw = None

    opts, args = getopt(sys.argv[1:], 'h:p:a:')
    for k, v in opts:
        if k == '-h':
            host = v
        elif k == '-p':
            port = int(v)
        elif k == '-a':
            pw = v

    if host is None:
        host = raw_input('Enter game server host IP/name: ')
    if port is None:
        port = int(raw_input('Enter host port: '))
    if pw is None:
        print "Enter the password if you want to run privileged commands"
        print "or just hit the Enter key"
        pw = getpass.getpass()

    try:
        try:
            serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            print 'Connecting to : %s:%d...' % ( host, port )
            serverSocket.connect( ( host, port ) )
            serverSocket.setblocking(1)
            
            receiveBuffer = ""
            if pw:

                # Retrieve this connection's 'salt' (magic value used when encoding password) from server
                getPasswordSaltRequest = EncodeClientRequest( [ "login.hashed" ] )
                serverSocket.send(getPasswordSaltRequest)

                [getPasswordSaltResponse, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
                #printPacket(DecodePacket(getPasswordSaltResponse))

                [isFromServer, isResponse, sequence, words] = DecodePacket(getPasswordSaltResponse)

                # if the server doesn't understand "login.hashed" command, abort
                if words[0] != "OK":
                    sys.exit(0);

                # Given the salt and the password, combine them and compute hash value
                salt = words[1].decode("hex")
                passwordHash = generatePasswordHash(salt, pw)
                passwordHashHexString = string.upper(passwordHash.encode("hex"))

                # Send password hash to server
                loginRequest = EncodeClientRequest( [ "login.hashed", passwordHashHexString ] )
                serverSocket.send(loginRequest)

                [loginResponse, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
                #printPacket(DecodePacket(loginResponse))

                [isFromServer, isResponse, sequence, words] = DecodePacket(loginResponse)

                # if the server didn't like our password, abort
                if words[0] != "OK":
                    [isFromServer, isResponse, sequence, words] = DecodePacket(loginResponse)
                    print words
                    sys.exit(0);

            print """\
 ____   _____    ____    ____  ____  
| __ ) |  ___|  | __ )  / ___||___ \ 
|  _ \ | |_   ()|  _ \ | |      __) |
| |_) ||  _|    | |_) || |___  / __/   
|____/ |_|    ()|____/  \____||_____|  v%s
                
             by %s                  
  ____                                                _             
 / ___| ___   _ __ ___   _ __ ___    __ _  _ __    __| |  ___  _ __ 
| |    / _ \ | '_ ` _ \ | '_ ` _ \  / _` || '_ \  / _` | / _ \| '__|
| |___| (_) || | | | | || | | | | || (_| || | | || (_| ||  __/| |   
 \____|\___/ |_| |_| |_||_| |_| |_| \__,_||_| |_| \__,_| \___||_|  
 
 Type 'help' to get the list of available commands
 Type 'help <cmd>' to get help on a given command
 Use the [TAB] key for command completion
 
            """ % (__version__, __author__)
            
            
            request = EncodeClientRequest(['version'])
            serverSocket.send(request)
            [packet, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
            [isFromServer, isResponse, sequence, words] = DecodePacket(packet)
            if words[0]=='OK':
                bfbc2version = int(words[2])
            
            c = Bfbc2Commander_R9()
                
            c.initSocket(serverSocket, receiveBuffer)
            c.cmdloop()


        except socket.error, detail:
            print 'Network error:', detail[1]

        except EOFError, KeyboardInterrupt:
            pass

        except:
            raise

    finally:
        try:
            if serverSocket is not None:
                serverSocket.close()
            print "Done"
        except:
            raise

    
if __name__ == '__main__':
    import traceback
    try:
        main()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except:
        traceback.print_exc()
        if main_is_frozen():
            raw_input('press the [Enter] key to exit')
        
    sys.exit( 0 )
