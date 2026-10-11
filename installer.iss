[Setup]
AppName=Bank Statement Converter
AppVersion=1.0.2
DefaultDirName={autopf}\Bank Statement Converter
DefaultGroupName=Bank Statement Converter
OutputDir=dist
OutputBaseFilename=BankStatementConverter_Setup
SetupIconFile=app_icon.ico
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\app_icon.ico

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\BankStatementConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Bank Statement Converter"; Filename: "{app}\BankStatementConverter.exe"; IconFilename: "{app}\BankStatementConverter.exe"
Name: "{autodesktop}\Bank Statement Converter"; Filename: "{app}\BankStatementConverter.exe"; IconFilename: "{app}\BankStatementConverter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\BankStatementConverter.exe"; Description: "{cm:LaunchProgram,Bank Statement Converter}"; Flags: nowait postinstall skipifsilent
