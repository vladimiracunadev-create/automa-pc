; ============================================================
;  Automa — Inno Setup installer
;  Empaqueta dist/Automa/ (output de PyInstaller) en un .exe
;  instalable estilo Windows. Crea shortcuts en Start Menu y
;  opcionalmente en el escritorio.
;
;  Build local (requiere Inno Setup 6+ en PATH):
;    1) pwsh installer/build_local.ps1   ; genera dist/Automa/
;    2) iscc installer/Automa.iss        ; genera installer/output/Automa-Setup-vX.Y.Z.exe
;
;  CI windows-latest (ver .github/workflows/release.yml):
;    Inno Setup viene preinstalado como 'iscc' en el runner.
; ============================================================

#define AppName "Automa"
#define AppPublisher "Vladimir Acuna"
#define AppURL "https://github.com/vladimiracunadev-create/automa-pc"
#define AppExeName "Automa.exe"
#define SourceDir "..\dist\Automa"

; AppVersion lo inyecta CI via /DAppVersion=X.Y.Z; default sirve para builds locales.
#ifndef AppVersion
  #define AppVersion "0.2.0"
#endif

[Setup]
AppId={{A0540AA3-1F2B-4D49-8C1E-AUTOMA00PC00}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=output
OutputBaseFilename=Automa-Setup-v{#AppVersion}
SetupIconFile=
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
