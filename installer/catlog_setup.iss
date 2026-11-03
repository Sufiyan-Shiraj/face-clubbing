; CatLog Windows Inno Setup Script (SPEC & BUILD_PLAN Phase V2-8)
; Produces CatLog-Setup-<Version>.exe for Windows x64.
; Packages the PyInstaller onedir distribution (dist/CatLog/) with:
; - Start Menu & Desktop shortcuts
; - Add/Remove Programs integration
; - Clean uninstaller removing application files and local cache
; - WebView2 runtime check & advisory

#ifndef MyAppVersion
#define MyAppVersion "0.1.0-rc1"
#endif

#define MyAppName "CatLog"
#define MyAppPublisher "CatLog Contributors"
#define MyAppURL "https://github.com/Sufiyan-Shiraj/face-clubbing"
#define MyAppExeName "CatLog.exe"
#define MyAppAssocName MyAppName + " Project"
#define MyAppAssocExt ".work"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; Basic Application Identification
AppId={{C4710C47-7106-4C53-839A-7F150CA7109E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Installation Directory (User directory fallback if non-admin)
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
InfoBeforeFile=
InfoAfterFile=

; Output Configuration
OutputDir=..\dist_release
OutputBaseFilename=CatLog-Setup-{#MyAppVersion}
SetupIconFile=..\catlog.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Privileges: allows regular user install without forcing elevation
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Visual Branding
DisableProgramGroupPage=yes
ChangesAssociations=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Distribute all files from dist\CatLog onedir folder
Source: "..\dist\CatLog\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\VERSION"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up cached thumbnails and temporary extract directories on uninstall
Type: filesandordirs; Name: "{app}\.cache"
Type: filesandordirs; Name: "{app}\*_temp"

[Code]
// Optional check for Microsoft Edge WebView2 Evergreen Runtime
function IsWebView2Installed(): Boolean;
var
  InstalledVersion: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-63D0-474E-9A57-F6CD33F63468}', 'pv', InstalledVersion) or
            RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-63D0-474E-9A57-F6CD33F63468}', 'pv', InstalledVersion);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not IsWebView2Installed() then
    begin
      Log('Notice: Microsoft Edge WebView2 runtime was not detected. CatLog uses WebView2 for its desktop interface.');
    end;
  end;
end;

