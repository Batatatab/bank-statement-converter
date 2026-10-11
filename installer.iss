; Inno Setup Script for Bank Statement Converter

[Setup]
AppId={{8E4F1823-99B7-4D93-9F9B-2E0F2B0759AA}
AppName=Bank Statement Converter
AppVersion=1.0.2
AppPublisher=Sharva Vinchurkar
DefaultDirName={autopf}\Bank Statement Converter
DefaultGroupName=Bank Statement Converter
OutputDir=dist_installer
OutputBaseFilename=BankStatementConverter_Setup
SetupIconFile=C:\Sharva\BS conv\app_icon.ico
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Grab everything generated inside the PyInstaller --onedir directory
Source: "C:\Sharva\BS conv\dist\BankStatementConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Sharva\BS conv\app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{autoprograms}\Bank Statement Converter"; Filename: "{app}\BankStatementConverter.exe"; IconFilename: "{app}\app_icon.ico"
; Desktop shortcut (Optional checkbox for user)
Name: "{autodesktop}\Bank Statement Converter"; Filename: "{app}\BankStatementConverter.exe"; Tasks: desktopicon; IconFilename: "{app}\app_icon.ico"

[Run]
; Option to launch immediately after finishing setup
Filename: "{app}\BankStatementConverter.exe"; Description: "{cm:LaunchProgram,Bank Statement Converter}"; Flags: nowait postinstall skipifsilent