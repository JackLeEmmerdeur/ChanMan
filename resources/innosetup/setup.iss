; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "ChanMan"
#define MyAppVersion "0.1"
#define MyAppPublisher "buccaneersdan"
#define MyAppURL "http://www.buccaneersdan.de"
#define MyAppExeName "ChanMan.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{F9A09629-E806-4133-A1E6-2E7D562C3D96}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\Buccaneersdan\ChanMan
DefaultGroupName=Buccaneersdan\ChanMan
OutputBaseFilename=setup
Compression=lzma
SolidCompression=yes

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\Buccaneersdan\Documents\Projekte\Python\sources\ChanMan\resources\pyinstaller\dist\ChanMan.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Buccaneersdan\Documents\Projekte\Python\sources\ChanMan\resources\pyinstaller\dist\innoadditional\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs 
; NOTE: Don't use "Flags: ignoreversion" on any shared system files
Source: "C:\Users\Buccaneersdan\Documents\Projekte\Python\sources\ChanMan\resources\binaries\yajl.dll"; DestDir: "{sys}"; Check: IsWin64; Flags: 64bit
; Flags: sharedfile

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

