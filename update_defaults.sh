#!/bin/bash

set -e

get_newest_rc_version() {
  versions=$(wget -q https://registry.hub.docker.com/v1/repositories/rocket.chat/tags -O- | sed -e 's/[][]//g' -e 's/"//g' -e 's/ //g' | tr '}' '\n'  | awk -F: '{print $3}')
  echo "${versions}" | tail -n1
}

if [ $# != 1 ]; then
  VERSION=$(get_newest_rc_version)
else
  VERSION=$1
fi

if [ -e "default_settings/${VERSION}.json" ]; then
    echo "Version ${VERSION} already exists"
    exit 0
fi

# Use different compose-files for versions < 1.0
if [[ $VERSION == 0* ]]; then
    sed "s/rocket.chat:latest/rocket.chat:${VERSION}/g" tests/docker-compose_lt-1.0.yaml > docker-compose_settings-update.yaml
else
    sed "s/rocket.chat:latest/rocket.chat:${VERSION}/g" tests/docker-compose_ge-1.0.yaml > docker-compose_settings-update.yaml
fi
docker-compose -f docker-compose_settings-update.yaml up -d

docker build -t settings_porter .

if ! docker run --net=rocketchat_settings_porter_default settings_porter test; then
  echo "Tests failed!"
  docker-compose -f docker-compose_settings-update.yaml down
  rm docker-compose_settings-update.yaml
  docker image prune -f
  exit 1
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
