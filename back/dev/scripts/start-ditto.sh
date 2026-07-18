if (!(Test-Path ".ditto")) {
    git clone https://github.com/eclipse-ditto/ditto.git .ditto
}

Set-Location .ditto/deployment/docker

docker compose up -d