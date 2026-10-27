#define MyAppName "ForexAI PRO"
#define MyAppVersion "1.2.3"
#define MyAppPublisher "Art010"
#define MyAppExeName "ForexAI_PRO.exe"
[Setup]
AppId={{D3D9FDD6-83F0-4927-A7FC-08E39288F3EB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\ForexAI PRO
DefaultGroupName=ForexAI PRO
OutputDir=installer_output
OutputBaseFilename=ForexAI_PRO_Setup_v1.2.3
SetupIconFile=ForexAI_PRO.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
[Languages]
Name: "thai"; MessagesFile: "compiler:Languages\Thai.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "desktopicon"; Description: "สร้างไอคอนบน Desktop"; GroupDescription: "ทางลัด:"; Flags: unchecked
[Files]
Source: "dist\ForexAI_PRO\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\ForexAI PRO"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\ForexAI PRO"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "เปิด ForexAI PRO"; Flags: postinstall nowait skipifsilent
