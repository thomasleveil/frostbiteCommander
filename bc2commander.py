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

__author__ = "Thomas Leveil <thomasleveil@gmail.com>"
__version__ = "1.0"


import string
import cmd
import socket
import readline
from CommandConsole import *



class Bfbc2Commander(cmd.Cmd):
    """BFBC2 command processor"""
    _socket = None
    _bfbc2cmdList = []
    _cmdsHelp = {}
    
    def __init__(self, socket):
        cmd.Cmd.__init__(self)
        self.prompt = '> '
        self._socket = socket
        self._initAvailableCmds()
        
    def _initAvailableCmds(self):
        words = self._sendBfbc2Cmd('help')
        if words[0] == 'OK':
            self._bfbc2cmdList = words[1:]
        else:
            self._bfbc2cmdList = ['login.hashed', 'login.plainText', 'logout', 'quit', 'serverInfo', 'version']
        
    def _sendBfbc2Cmd(self, command):
        words = shlex.split(command)

        if len(words) >= 1:

            if "quit" == words[0]:
                sys.exit(0)

            # Send request to server on command channel
            request = EncodeClientRequest(words)
            self._socket.send(request)

            # Wait for response from server
            packet = self._socket.recv(4096)    

            [isFromServer, isResponse, sequence, words] = DecodePacket(packet)

            # The packet from the server should 
            # For now, we always respond with an "OK"
            if not isResponse:
                print 'Received an unexpected request packet from server, ignored:'

            #printPacket(DecodePacket(packet))
            return words
    

    def emptyline(self):
        pass
        
    def default(self, line):
        words = self._sendBfbc2Cmd(line)
        print words
        
        if line.startswith(('login.plainText','logout')) and words[0]=='OK':
            self._initAvailableCmds()
    
    def completenames(self, text, *ignored):
        cmds = self._bfbc2cmdList
        if 'help' not in cmds:
            cmds.insert(0, 'help')
        return [a for a in cmds if a.lower().startswith(text.lower())]

    
    def do_help(self, arg):
        if arg:
            try:
                doc = self._cmdsHelp[arg]
                if doc:
                    self.stdout.write("%s\n"%str(doc))
                    return
            except KeyError:
                cmd.Cmd.do_help(self, arg)
        else:
            print "Available commands :"
            self.columnize(self._bfbc2cmdList, 80-1)
        
    def do_EOF(self, arg):
        raise SystemExit

class DocumentedBfbc2Commander(Bfbc2Commander):
    _cmdsHelp = {
 "login.plainText": """\
Request: login.plainText <password: string> 
Response: OK - Login successful, you are now logged in regardless of prior status 
Response: InvalidPassword - Login unsuccessful, logged-in status unchanged 
Response: PasswordNotSet - Login unsuccessful, logged-in status unchanged 
Response: InvalidArguments
Effect: Attempt to login to game server with password <password> 
Comments: If you are connecting to the admin interface over the internet, then use login.hashed instead to avoid having evildoers sniff the admin password
""",
"login.hashed": """\
Request: login.hashed 
Response: OK <salt: HexString> - Retrieved salt for the current connection 
Response: PasswordNotSet - No password set for server, login impossible 
Response: InvalidArguments Effect: Retrieves the salt, used in the hashed password login process 
Comments: This is step 1 in the 2-step hashed password process. When using this people cannot sniff your admin password.

Request: login.hashed <passwordHash: HexString> 
Response: OK - Login successful, you are now logged in regardless of prior status 
Response: PasswordNotSet - No password set for server, login impossible 
Response: InvalidPasswordHash - Login unsuccessful, logged-in status unchanged 
Response: InvalidArguments Effect: Sends a hashed password to the server, in an attempt to log in 
Comments: This is step 2 in the 2-step hashed password process. When using this people cannot sniff your admin password.
""",
"logout": """\
Request: logout 
Response: OK - You are now logged out regardless of prior status 
Response: InvalidArguments 
Effect: Logout from game server
""",
"quit": """\
Request: quit 
Response: OK 
Response: InvalidArguments 
Effect: Disconnect from server
""",
"version": """\
Request: version 
Response: OK BFBC2 <version> 
Response: InvalidArguments 
Effect: Reports game server type, and build ID 
Comments: Game server type and build ID uniquely identify the server, and the protocol it is running.
""",
"eventsEnabled": """\
Request: eventsEnabled [enabled: boolean] 
Response: OK - for set operation 
Response: OK <enabled: boolean> - for get operation 
Response: InvalidArguments 
Effect: Set whether or not the server will send events to the current connection
""",
"help": """\
Request: help 
Response: OK <all commands availble on server, as separate words> 
Response: InvalidArguments 
Effect: Report which commands the server knows about
""",
"admin.runScript": """\
Request: admin.runScript <filename: filename> 
Response: OK 
Response: InvalidArguments 
Response: InvalidFileName - The filename specified does not follow filename rules 
Response: ScriptError <line> <original error…> - Script failed at line <line>, with the given error 
Effect: Process file, executing script lines one-by-one, aborting processing upon error
""",
"punkBuster.pb_sv_command": """\
Request: punkBuster.pb_sv_command <command: string> 
Response: OK - Command sent to PunkBuster server module 
Response: InvalidArguments 
Response: InvalidPbServerCommand - Command does not begin with “pb_sv_” 
Effect: Send a raw PunkBuster command to the PunkBuster server Comment: The entire command is to be sent as a single string. Don’t split it into multiple words.
""",
"serverInfo": """\
Request: serverInfo 
Response: OK <serverName> <current playercount> <max playercount> <current gamemode> <current map> 
Response: InvalidArguments 
Effect: Query for brief server info. 
Comments: This command can be performed without being logged in.
""",
"admin.yell": """\
Request: admin.yell <message: string> <duration [in ms]: integer> <players: player subset>
Response: OK
Response: InvalidArguments
Response: TooLongMessage
Response: InvalidDuration
Effect: Display a message, very visibly on players’ screens, for a certain amount of time. The duration must be more than 0 and at most 60000 ms. The message must be less than 100 characters long.
""",
"admin.runNextLevel": """\
Request: admin.runNextLevel
Response: OK
Response: InvalidArguments
Effect: Switch to next level
Comments: Always successful
""",
"admin.currentLevel": """\
Request: admin.currentLevel
Response: OK <name>
Response: InvalidArguments
Effect: Return current level name
""",
"admin.nextLevel": """\
Request: admin.nextLevel <name: string> ##QA: Not working
Response: OK
Response: InvalidArguments
Response: InvalidLevelName - Level not available on server
Effect: Set name of next level to be run to <name>
""",
"admin.restartMap": """\
Request: admin.restartMap
Response: OK
Response: InvalidArguments
Response: LevelNotAvailable - server currently has no level loaded / level not available on server
Effect: End current round, and restart with the same map
""",
"admin.supportedMaps": """\
Request: admin.supportedMaps <play list: string> ##QA: Does not give maps names
Response: OK <map names>
Response: InvalidArguments
Response: InvalidPlaylist <play list> - Play list doesn't exist on server
Effect: Retrieve maplist of maps supported in this play list
""",
"admin.setPlaylist": """\
Request: admin.setPlaylist <name: string>
Response: OK - Play list was changed
Response: InvalidArguments
Response: InvalidPlaylist - Play list doesn't exist on server
Effect: Set the play list on the server.
Comments: Will only use maps supported for this play list. So the mapList might be invalid Delay: Change occurs after end of round
""",
"admin.getPlaylist": """\
Request: admin.getPlaylist <name: string>
Response: OK <play list>
Response: InvalidArguments
Effect: Get the current play list for the server
""",
"admin.getPlaylists": """\
Request: admin.getPlaylists
Response: OK <play lists>
Response: InvalidArguments
Effect: Get the play lists for the server
""",
"admin.kickPlayer": """\
Request: admin.kickPlayer <soldier name: player name>
Response: OK - Player did exist, and got kicked
Response: InvalidArguments
Response: PlayerNotFound - Player name doesn't exist on server
Effect: Kick player <soldier name> from server
""",
"admin.listPlayers": """\
Request: admin.listPlayers <players: player subset>
Response: OK <matching players: N x player info> player info format: <clanTag: clantag> <player name: player name> <squad: squadID> <team: teamID>
Response: InvalidArguments
Effect: Return list of all players on the server
""",
"admin.banPlayer": """\
Request: admin.banPlayer <soldier name: player name> <timeout: timeout>
Response: OK
Response: InvalidArguments
Effect: Add player to ban list for a certain amount of time
Comments: Adding a new player ban will replace any previous ban for that player name timeout can take three forms: perm - permanent [default] round - until end of round seconds <integer> - number of seconds until ban expires Adding the same player multiple times, with different timeouts, is possible
""",
"admin.banIP": """\
Request: admin.banIP <IP address: string> <timeout: timeout>
Response: OK
Response: InvalidArguments
Effect: Add IP address to ban list for a certain amount of time Adding a new IP ban will replace any previous ban for that IP
Comments: IP address should be specified on xxx.xxx.xxx.xxx format timeout can take three forms; see admin.banPlayer for details Adding the same player multiple times, with different timeouts, is possible
""",
"admin.unbanPlayer": """\
Request: admin.unbanPlayer <soldier name: player name>
Response: OK
Response: InvalidArguments
Response: PlayerNotFound - Player name not found in banlist; banlist unchanged
Effect: Remove player name from banlist
""",
"admin.unbanIP": """\
Request: admin.unbanIP <IP address: string>
Response: OK
Response: InvalidArguments
Response: IPNotFound - IP address not found in banlist; banlist unchanged
Effect: Remove IP address from banlist
""",
"admin.clearPlayerBanList": """\
Request: admin.clearPlayerBanList
Response: OK
Response: InvalidArguments
Effect: Clears player name ban list
""",
"admin.clearIPBanList": """\
Request: admin.clearIPBanList
Response: OK
Response: InvalidArguments
Effect: Clears IP number ban list
""",
"admin.listPlayerBans": """\
Request: admin.listPlayerBans
Response: OK <player ban entries>
Response: InvalidArguments
Effect: Return list of banned players. The list is currently a single, long string in a very ugly format.
Comment: It might turn into a cleaner format sometime in the future.
""",
"admin.listIPBans": """\
Request: admin.listIPBans
Response: OK <IP ban entries>
Response: InvalidArguments
Effect: Return list of banned players. The list is currently a single, long string in a very ugly format.
Comment: It might turn into a cleaner format sometime in the future.
""",
"reservedSlots.configFile": """\
Request: reservedSlots.configFile [filename: filename] - disabled for security reasons atm
Response: OK - for set option
Response: OK <filename> - for get option
Response: InvalidArguments
Response: InvalidFileName - Filename does not follow filename rules
Effect: Set name of reserved slots configuration file
""",
"reservedSlots.load": """\
Request: reservedSlots.load
Response: OK
Response: InvalidArguments
Response: AccessError - File not found; internal reserved slots list is now empty
Effect: Load list of soldier names from file. This is a file with one soldier name per line. If loading succeeds, the reserved slots list will get updated. If loading fails, the reserved slots list will remain unchanged.
""",
"reservedSlots.save": """\
Request: reservedSlots.save
Response: OK
Response: InvalidArguments
Response: AccessError - Error while saving
Effect: Save list of reserved soldier names to file. This is a file with one soldier name per line.
Comment: If saving fails, the output file may be unchanged or corrupt.
""",
"reservedSlots.addPlayer": """\
Request: reservedSlots.addPlayer <soldier name: player name>
Response: OK
Response: InvalidArguments
Response: PlayerAlreadyInList - Player is already in the list; reserved slots list unchanged
Effect: Add <soldier name> to list of players who can use the reserved slots.
""",
"reservedSlots.removePlayer": """\
Request: reservedSlots.removePlayer <soldier name: player name>
Response: OK
Response: InvalidArguments
Response: PlayerNotInList - Player does not exist in list; reserved slots list unchanged
Effect: Remove <soldier name> from list of players who can use the reserved slots.
""",
"reservedSlots.clear": """\
Request: reservedSlots.clear
Response: OK
Response: InvalidArguments
Effect: Clear reserved slots list
""",
"reservedSlots.list": """\
Request: reservedSlots.list
Response: OK <soldier names>
Response: InvalidArguments
Effect: Retrieve list of players who can utilize the reserved slots
""",
"mapList.configFile": """\
Request: mapList.configFile [filename: filename] - disabled for security reasons atm
Response: OK - for set option
Response: OK <filename> - for get option
Response: InvalidArguments
Response: InvalidFileName - Filename does not follow filename rules
Effect: Set name of maplist configuration file
""",
"mapList.load": """\
Request: mapList.load
Response: OK - Maplist loaded
Response: InvalidArguments
Response: AccessError - File not found, internal maplist is now empty
Response: InvalidMapName <name> - Map with name <name> doesn't exist on server
Effect: Load list of map names from file. This is a file with one map name per line.
Comments: If loading succeeds, the maplist will get updated. If loading fails, the maplist will remain unchanged.
""",
"mapList.save": """\
Request: mapList.save
Response: OK - Maplist saved
Response: InvalidArguments
Response: AccessError - Error while saving, on-disk maplist file possibly corrupted now
Effect: Save maplist to file. This is a file with one map name per line.
Comments: If saving fails, the output file may be unchanged or corrupt.
""",
"mapList.list": """\
Request: mapList.list ##QA: Says ‘OK’ but does not show maplist
Response: OK <map names>
Response: InvalidArguments
Effect: Retrieve current maplist
""",
"mapList.clear": """\
Request: mapList.clear
Response: OK
Response: InvalidArguments
Effect: Clears maplist
Comments: If server attempts to switch level while maplist is cleared, nasty things will happen
""",
"mapList.remove": """\
Request: mapList.remove <name: string> ##QA: Does not work!
Response: OK - Map removed from list
Response: InvalidArguments
Response: InvalidMapName - Map doesn't exist on server
Effect: Remove map from list.
Comments: bounds, the counter will be reset to 0.
""",
"mapList.append": """\
Request: mapList.append <name: string> ##QA: Does not work!
Response: OK - Map appended to list
Response: InvalidArguments
Response: InvalidMapName - Map doesn't exist on server
Effect: Add map with name <name> to end of maplist
""",
"vars.adminPassword": """\
Request: vars.adminPassword [password: password]
Response: OK - for set operation
Response: OK <password> - for get operation
Response: InvalidArguments
Response: InvalidPassword - password does not conform to password format rules
Effect: Set the admin password for the server, use it with an empty string("") to reset
""",
"vars.gamePassword": """\
Request: vars.gamePassword [password: password]
Response: OK - for set operation
Response: OK <password> - for get operation
Response: InvalidArguments
Response: InvalidPassword - password does not conform to password format rules
Effect: Set the game password for the server, use it with an empty string("") to reset
""",
"vars.punkBuster": """\
Request: vars.punkBuster [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Effect: Set if the server will use PunkBuster or not
""",
"vars.hardCore": """\
Request: vars.hardCore [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Effect: Set hardcore mode Delay: Works after map change
""",
"vars.ranked": """\
Request: vars.ranked [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation Response InvalidArguments
Effect: Set ranked or not
""",
"vars.rankLimit": """\
Request: vars.rankLimit <rank: integer> ##QA: Says ‘OK’ but still allow higher ranked players to join
Response: OK - for set operation
Response: OK <rank: integer> - for get operation
Response: InvalidArguments
Effect: Set the highest rank allowed on to the server (integer value).
Comment: To disable rank limit use -1 as value
""",
"vars.teamBalance": """\
Request: vars.teamBalance [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Effect: Set if the server should autobalance
""",
"vars.friendlyFire": """\
Request: vars.friendlyFire [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Effect: Set if the server should allow team damage Delay: Works after round restart
""",
"vars.currentPlayerLimit": """\
Request: vars.currentPlayerLimit
Response: OK <nr of players: integer> - for get operation
Response: ReadOnly - if you try to send any arguments
Response: InvalidArguments
Effect: Retrieve the current maximum number of players
Comment: This value is computed from all the different player limits in effect at any given moment
""",
"vars.maxPlayerLimit": """\
Request: vars.maxPlayerLimit
Response: OK <nr of players: integer> - for get operation
Response: ReadOnly - if you try to send any arguments
Response: InvalidArguments
Effect: Retrieve the server-enforced maximum number of players
Comment: Setting the user-defined maximum number of players higher than this has no effect
""",
"vars.playerLimit": """\
Request: vars.playerLimit [nr of players: integer]
Response: OK - for set operation
Response: OK <nr of players: integer> - for get operation
Response: InvalidArguments
Response: InvalidNrOfPlayers - Player limit must be in the range 8..32
Effect: Set desired maximum number of players
Comment: The effective maximum number of players is also effected by the server provider, and the game engine
""",
"vars.bannerUrl": """\
Request: vars.bannerUrl [url: string]
Response: OK - for set operation
Response: OK <url: string> - for get operation
Response: InvalidArguments
Response: TooLongUrl - for set operation
Effect: Set banner url
Comment: The banner url needs to be less than 64 characters long The banner needs to be a 512x64 picture smaller than 127kb Example: admin.setBannerUrl http://www.example.com/banner.jpg
""",
"vars.serverDescription": """\
Request: vars.serverDescription <description: string>
Response: OK - for set operation
Response: OK <description: string> - for get operation
Response: InvalidArguments
Response: TooLongDescription - for set operation
Effect: Set server description
Comment: The description needs to be less than 400 characters long
##Request from RSPs: In addition being able to enter a new line would be great, BF2142 used the "|" character as newline.
""",
"vars.killCam": """\
Request: vars.killCam [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Effect: Set if killcam is enabled Delay: Works after map switch
""",
"vars.miniMap": """\
Request: vars.miniMap [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Effect: Set if minimap is enabled Delay: Works after map switch
""",
"vars.crossHair": """\
Request: vars.crossHair [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Effect: Set if crosshair for all weapons is enabled Delay: Works after map switch
""",
"vars.3dSpotting": """\
Request: vars.3dSpotting [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Effect: Set if spotted targets are visible in the 3d-world Delay: Works after map switch
""",
"vars.miniMapSpotting": """\
Request: vars.miniMapSpotting [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Effect: Set if spotted targets are visible on the minimap Delay: Works after map switch
""",
"vars.thirdPersonVehicleCameras": """\
Request: vars.thirdPersonVehicleCameras [enabled: boolean]
Response: OK - for set operation
Response: OK <enabled: boolean> - for get operation
Response: InvalidArguments
Effect: <todo> Delay: Works after map switch
##QA: Works but is bugged. If you change the setting and someone is in a vehicle in 3rd person view when at end of round, that player will be stuck in 3rd person view even though the setting should only allow 1st person view.
""",
     }


def main_is_frozen():
    """detect if the script is running from frozen
    distribution. i.e: from a py2exe build or others
    """
    return (hasattr(sys, "frozen") or # new py2exe
        hasattr(sys, "importers") or # old py2exe
        imp.is_frozen("__main__")) # tools/freeze

        
def main():
    from getopt import getopt
    import sys
    import getpass

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

            print 'Connecting to port: %s:%d...' % ( host, port )
            serverSocket.connect( ( host, port ) )
            serverSocket.setblocking(1)

            if pw:

                # Retrieve this connection's 'salt' (magic value used when encoding password) from server
                getPasswordSaltRequest = EncodeClientRequest( [ "login.hashed" ] )
                serverSocket.send(getPasswordSaltRequest)

                getPasswordSaltResponse = serverSocket.recv(4096)
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

                loginResponse = serverSocket.recv(4096)    
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
            
            DocumentedBfbc2Commander(serverSocket).cmdloop()


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
    except:
        traceback.print_exc()
        if main_is_frozen():
            raw_input('press the [Enter] key to exit')
        
    sys.exit( 0 )
