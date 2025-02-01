# scripts/generate-client.ps1
$env:PYTHONPATH = "backend"

# Executa o Python e armazena a saída na variável $openapi
$openapi = python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))"

# Grava o conteúdo em openapi.json sem BOM
[System.IO.File]::WriteAllText(
    "openapi.json",
    $openapi,
    (New-Object System.Text.UTF8Encoding($false))  # $false => sem BOM
)

node .\frontend\modify-openapi-operationids.js

Move-Item -Path .\openapi.json -Destination .\frontend\ -Force

Set-Location .\frontend\
npm run generate-client
npx biome format --write .\src\client

# Volta pra raiz do projeto (opcional)
Set-Location ..
