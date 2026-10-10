# Tag and push wealthplanner to Docker Hub (or compatible registry).
# Usage:
#   docker login
#   .\scripts\docker-push.ps1 YOUR_DOCKERHUB_USERNAME
# Optional second arg is tag (default latest):
#   .\scripts\docker-push.ps1 YOUR_DOCKERHUB_USERNAME v1.0.0

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $DockerHubUser,
    [Parameter(Position = 1)]
    [string] $Tag = "latest"
)

$ErrorActionPreference = "Stop"
$src = "wealthplanner:$Tag"
$dst = "${DockerHubUser}/wealthplanner:${Tag}"

docker image inspect $src 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Building image first..."
    $repoRoot = Split-Path $PSScriptRoot -Parent
    Push-Location $repoRoot
    try {
        docker compose build web
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Tagging $src -> $dst"
docker tag $src $dst
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Pushing $dst"
docker push $dst
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Done: $dst"
