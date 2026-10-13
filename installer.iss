[Setup]
AppId={{8E4F1823-99B7-4D93-9F9B-2E0F2B0759AA}
AppName=Bank Statement Converter
AppVersion=1.1.0
AppPublisher=Batata
DefaultDirName={autopf}\Bank Statement Converter
DefaultGroupName=Bank Statement Converter
OutputDir=dist_installer
OutputBaseFilename=BankStatementConverter_Setup
SetupIconFile=app_icon.ico
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Uses clean relative paths matching the project root
Source: "dist\BankStatementConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Bank Statement Converter"; Filename: "{app}\BankStatementConverter.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\Bank Statement Converter"; Filename: "{app}\BankStatementConverter.exe"; Tasks: desktopicon; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "{app}\BankStatementConverter.exe"; Description: "{cm:LaunchProgram,Bank Statement Converter}"; Flags: nowait postinstall skipifsilent