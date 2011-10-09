; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!


;#define Debug
#define VersionNumber "4.1"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{5CA1C72F-72C2-4B61-AF76-9B2274186AA7}
AppName=FrostbiteCommander
AppVerName=FrostbiteCommander {#VersionNumber}
AppPublisher=FrostbiteCommander
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=
DefaultDirName={pf}\FrostbiteCommander
DefaultGroupName=Frostbite Commander
LicenseFile=LICENSE.txt
OutputBaseFilename=FrostbiteCommander_setup
Compression=lzma/ultra
SolidCompression=true
InternalCompressLevel=normal
DisableStartupPrompt=true
SetupLogging=true
VersionInfoVersion={#VersionNumber}
VersionInfoDescription=Frostbite Commander
VersionInfoCopyright=
AppCopyright=
VersionInfoTextVersion={#VersionNumber}
VersionInfoProductName=FrostbiteCommander
VersionInfoProductVersion={#VersionNumber}
ExtraDiskSpaceRequired=5750520
RestartIfNeededByRun=false
PrivilegesRequired=none
WizardImageBackColor=clBlack
WindowVisible=false
BackColor=clBlack
BackColor2=clYellow
UsePreviousAppDir=false

[Languages]
Name: english; MessagesFile: compiler:Default.isl
Name: basque; MessagesFile: compiler:Languages\Basque.isl
Name: brazilianportuguese; MessagesFile: compiler:Languages\BrazilianPortuguese.isl
Name: catalan; MessagesFile: compiler:Languages\Catalan.isl
Name: czech; MessagesFile: compiler:Languages\Czech.isl
Name: danish; MessagesFile: compiler:Languages\Danish.isl
Name: dutch; MessagesFile: compiler:Languages\Dutch.isl
Name: finnish; MessagesFile: compiler:Languages\Finnish.isl
Name: french; MessagesFile: compiler:Languages\French.isl
Name: german; MessagesFile: compiler:Languages\German.isl
Name: hebrew; MessagesFile: compiler:Languages\Hebrew.isl
Name: hungarian; MessagesFile: compiler:Languages\Hungarian.isl
Name: italian; MessagesFile: compiler:Languages\Italian.isl
Name: norwegian; MessagesFile: compiler:Languages\Norwegian.isl
Name: polish; MessagesFile: compiler:Languages\Polish.isl
Name: portuguese; MessagesFile: compiler:Languages\Portuguese.isl
Name: russian; MessagesFile: compiler:Languages\Russian.isl
Name: slovak; MessagesFile: compiler:Languages\Slovak.isl
Name: slovenian; MessagesFile: compiler:Languages\Slovenian.isl
Name: spanish; MessagesFile: compiler:Languages\Spanish.isl

[Icons]
Name: {group}\{cm:executable,bc2commander.exe}; Filename: {app}\frostbiteCommander.exe; WorkingDir: {app}; Flags: dontcloseonexit; Comment: Run BFBC2 Commander
Name: {group}\{cm:website,Website}; Filename: http://courgette.github.com/frostbiteCommander/; Comment: visit the Frostbite Commander website
Name: {group}\{cm:UninstallProgram,Uninstall}; Filename: {uninstallexe}

[Dirs]

[Files]
Source: dist\*; DestDir: {app}; Flags: recursesubdirs




[Components]


[UninstallDelete]
Name: {app}\*; Type: filesandordirs


[CustomMessages]
executable=Frostbite Commander
website=Website
