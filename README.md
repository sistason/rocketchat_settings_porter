# rocketchat_settings_porter

Import and Export Rocketchat-settings via the API. Enables config-management via CI/CD.

## Dependencies

- python3
- python3-requests
- [rocketchat_API](https://github.com/jadolg/rocketchat_API)
- (Docker + docker-compose)

## Usage

Run as a container besides your rocketchat-instance with a Dockerfile like included. 

Configure with the environment variables `API_HOST` (http://rocketchat:3000), `API_USER`, `API_PASS`, 
`SETTINGS_PATH` (location of the export/import json) and the volume mounted at the settings_path.

Start with the args:
- "import": Import all settings from the mounted file
- "export_all": Export all current settings to the mounted file
- "export_changed": Export only settings with non-default-values to the mounted file
- "test": Test the functionality. See below.

## Test

The `docker-compose_*.yaml` in the tests/ directory starts a rocketchat-server.
As the interaction with MongoDB changed since RC v1.0, use the compose file depending on your version of rocketchat.
Then, run the exporter with the argument `test`.

## Meta-Build

To keep the defaults up-to-date when a new rocketchat-version is released, the `update_defaults.sh` is run
on a server commiting and pushing new default-files to the repo, which will be rebuild by Docker Hub.
