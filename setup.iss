; ============================================================
; 专利证书可见内容核验系统 — Inno Setup 安装脚本
; 基于 PyInstaller 打包，Win7/Win10 兼容
; ============================================================

#define MyAppName "专利证书核验系统"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "PatentVerify"
#define MyAppExeName "专利证书核验系统.exe"
#define MySourceDir "..\dist\专利证书核验系统"

[Setup]
AppId={{B8F4A2D1-9C6E-4A3B-8F12-D5E7A0B3C4F9}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=专利证书核验系统_v2.0.0_Win7_安装包
Compression=lzma2/ultra64
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
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "额外图标:"

[Files]
Source: "{#MySourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "launcher.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MySourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\chrome\Chrome_109.0.5414.120_64bit.exe"; DestDir: "{app}\chrome"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

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
