; ============================================================
; 专利证书核验系统 — 升级补丁包
; 只替换改动的文件，保留已有依赖
; ============================================================

#define MyAppName "专利证书核验系统"
#define MyAppVersion "2.0.1"
#define MyAppExeName "专利证书核验系统.exe"
#define MySourceDir "..\dist\专利证书核验系统"

[Setup]
AppId={{B8F4A2D1-9C6E-4A3B-8F12-D5E7A0B3C4F9}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=PatentVerify
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=专利证书核验系统_v2.0.1_升级补丁
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
MinVersion=6.1sp1
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
Uninstallable=no


[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
; === 核心代码更新（关键修复）===
Source: "{#MySourceDir}\_internal\backend\skills\*.py"; DestDir: "{app}\_internal\backend\skills"; Flags: ignoreversion recursesubdirs
Source: "{#MySourceDir}\_internal\backend\routers\*.py"; DestDir: "{app}\_internal\backend\routers"; Flags: ignoreversion recursesubdirs
Source: "{#MySourceDir}\_internal\backend\*.py"; DestDir: "{app}\_internal\backend"; Flags: ignoreversion recursesubdirs


; === CV2 修复（opencv-python-headless 4.9.0，解决 OCR 崩溃）===
Source: "{#MySourceDir}\_internal\cv2\*"; DestDir: "{app}\_internal\cv2"; Flags: ignoreversion recursesubdirs createallsubdirs

; === 前端更新 ===
Source: "{#MySourceDir}\_internal\frontend\dist\*"; DestDir: "{app}\_internal\frontend\dist"; Flags: ignoreversion recursesubdirs createallsubdirs

; === 主程序更新 ===
Source: "{#MySourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "额外图标:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

