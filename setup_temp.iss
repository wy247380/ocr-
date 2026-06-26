; ============================================================
; 涓撳埄璇佷功鍙鍐呭鏍搁獙绯荤粺 鈥?Inno Setup 瀹夎鑴氭湰
; 鍩轰簬 PyInstaller 鎵撳寘锛學in7/Win10 鍏煎
; ============================================================

#define MyAppName "涓撳埄璇佷功鏍搁獙绯荤粺"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "PatentVerify"
#define MyAppExeName "涓撳埄璇佷功鏍搁獙绯荤粺.exe"
#define MySourceDir "..\dist\涓撳埄璇佷功鏍搁獙绯荤粺"

[Setup]
AppId={{B8F4A2D1-9C6E-4A3B-8F12-D5E7A0B3C4F9}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=涓撳埄璇佷功鏍搁獙绯荤粺_v2.0.0_Win7_瀹夎鍖?Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
MinVersion=6.1sp1
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "鍒涘缓妗岄潰蹇嵎鏂瑰紡"; GroupDescription: "棰濆鍥炬爣:"

[Files]
Source: "{#MySourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MySourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\chrome\Chrome_109.0.5414.120_64bit.exe"; DestDir: "{app}\chrome"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\鍗歌浇 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "鍚姩 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    ForceDirectories(ExpandConstant('{app}\data\uploads'));
    ForceDirectories(ExpandConstant('{app}\chrome'));
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\{#MyAppExeName}"
Type: filesandordirs; Name: "{app}\data"
Type: dirifempty; Name: "{app}"
