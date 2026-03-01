; GlamConnect Installer Script
; Built with Inno Setup — https://jrsoftware.org/isinfo.php

[Setup]
AppName=GlamConnect
AppVersion=1.0.0
AppPublisher=GlamConnect
AppPublisherURL=http://127.0.0.1:8765
AppSupportURL=http://127.0.0.1:8765
AppComments=Makeup Artist Booking Platform

; Install to user's local AppData — no admin rights required
DefaultDirName={localappdata}\GlamConnect
DefaultGroupName=GlamConnect
PrivilegesRequired=lowest

; Output
OutputDir=installer
OutputBaseFilename=GlamConnect_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Version info shown in Windows "About" / Properties
VersionInfoVersion=1.0.0.0
VersionInfoCompany=GlamConnect
VersionInfoDescription=GlamConnect Makeup Booking Platform
VersionInfoProductName=GlamConnect
VersionInfoProductVersion=1.0.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; The main executable
Source: "backend\dist\GlamConnect.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\GlamConnect"; Filename: "{app}\GlamConnect.exe"; Comment: "Launch GlamConnect Booking Platform"
; Desktop shortcut (only if user ticked the task above)
Name: "{userdesktop}\GlamConnect"; Filename: "{app}\GlamConnect.exe"; Comment: "Launch GlamConnect Booking Platform"; Tasks: desktopicon

[Run]
; Allow GlamConnect through Windows Firewall so phones can connect (runs silently)
Filename: "netsh.exe"; Parameters: "advfirewall firewall delete rule name=""GlamConnect Server"""; Flags: runhidden; StatusMsg: "Configuring network..."
Filename: "netsh.exe"; Parameters: "advfirewall firewall add rule name=""GlamConnect Server"" dir=in action=allow protocol=TCP localport=8765 description=""Allows GlamConnect to be accessed from phones on your WiFi"""; Flags: runhidden; StatusMsg: "Configuring network..."

; Offer to launch the app immediately after install
Filename: "{app}\GlamConnect.exe"; Description: "Launch GlamConnect now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove firewall rule on uninstall
Filename: "netsh.exe"; Parameters: "advfirewall firewall delete rule name=""GlamConnect Server"""; Flags: runhidden

[UninstallDelete]
; Clean up the data folder on uninstall
Type: filesandordirs; Name: "{localappdata}\GlamConnect"
