# Installe le skill suivi-module dans le projet courant (.claude\skills).
# Pour tous vos projets : définir $env:SUIVI_MODULE_GLOBAL = "1" avant de lancer.
$ErrorActionPreference = "Stop"
$Repo = if ($env:SUIVI_MODULE_REPO) { $env:SUIVI_MODULE_REPO } else { "dav9fulldev/suivi-module-skill" }
$Ref  = if ($env:SUIVI_MODULE_REF)  { $env:SUIVI_MODULE_REF }  else { "main" }
$Dest = if ($env:SUIVI_MODULE_GLOBAL -eq "1") { Join-Path $HOME ".claude\skills" } else { Join-Path (Get-Location) ".claude\skills" }

$Tmp = Join-Path ([IO.Path]::GetTempPath()) ("suivi-module-" + [Guid]::NewGuid())
New-Item -ItemType Directory -Path $Tmp | Out-Null
try {
  $Zip = Join-Path $Tmp "depot.zip"
  Invoke-WebRequest -Uri "https://codeload.github.com/$Repo/zip/refs/heads/$Ref" -OutFile $Zip -UseBasicParsing
  Expand-Archive -Path $Zip -DestinationPath $Tmp
  $Src = Get-ChildItem -Path $Tmp -Directory -Recurse -Depth 2 |
         Where-Object { $_.Name -eq "suivi-module" -and $_.Parent.Name -eq "skills" } | Select-Object -First 1
  if (-not $Src -or -not (Test-Path (Join-Path $Src.FullName "SKILL.md"))) { throw "Skill introuvable dans l'archive de $Repo." }
  New-Item -ItemType Directory -Path $Dest -Force | Out-Null
  $Cible = Join-Path $Dest "suivi-module"
  if (Test-Path $Cible) { Remove-Item -Recurse -Force $Cible }
  Copy-Item -Recurse -Path $Src.FullName -Destination $Cible
  Write-Host "Skill suivi-module installé dans $Cible"
  Write-Host "Dans Claude Code, demandez par exemple : « crée le tableau de suivi de mon module »."
} finally {
  Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
}
