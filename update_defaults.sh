#!/bin/bash

if [ $# != 1 ]; then
  all_versions=$(wget -q https://registry.hub.docker.com/v1/repositories/rocket.chat/tags -O- | jq -r '.[] | .name' | tail -n +150)
else
  all_versions="$1"
fi

function main {
    VERSION=${1}

    echo "generating default settings for version \"${version}\""...

    # Use different compose-files for versions < 1.0
    if [[ $VERSION == 0* ]]; then
        sed "s/rocket.chat:latest/rocket.chat:${VERSION}/g" tests/docker-compose_lt-1.0.yaml > docker-compose_settings-update.yaml
    else
        sed "s/rocket.chat:latest/rocket.chat:${VERSION}/g" tests/docker-compose_ge-1.0.yaml > docker-compose_settings-update.yaml
    fi
    docker-compose -f docker-compose_settings-update.yaml pull
    if [[ $? != 0 ]]; then
        echo "pseudo tag on docker-hub, skipping..."
        docker image prune -f
        return
    fi

    docker-compose -f docker-compose_settings-update.yaml up -d

    docker build -t settings_porter .

    echo "Running tests..."
    if ! docker run --net=rocketchat_settings_porter_default settings_porter test; then
      echo "Tests failed!"
      docker-compose -f docker-compose_settings-update.yaml down
      rm docker-compose_settings-update.yaml
      docker image prune -f
      return
    fi

    touch "default_settings/${VERSION}.json"

    if docker run -v "$(pwd)/default_settings/${VERSION}.json:/settings.json" --net=rocketchat_settings_porter_default \
                  -e API_USER="admin" -e API_HOST="http://rocketchat:3000" \
                  -e API_PASS="foobarbaz" -e SETTINGS_PATH="/settings.json" settings_porter export_all; then

      git add "default_settings/${VERSION}.json"
      git commit "default_settings/${VERSION}.json" -m"Automatic update of defaults for version ${VERSION}"
      git push
    fi

    if [ ! -s "default_settings/${VERSION}.json" ]; then
      rm "default_settings/${VERSION}.json"
    fi
    docker-compose -f docker-compose_settings-update.yaml down
    rm docker-compose_settings-update.yaml
    docker image prune -f
}

for version in $all_versions; do
    if [ -e "default_settings/${version}.json" ]; then
        echo "Version ${version} already exists"
        continue
    fi

    main ${version}
done

