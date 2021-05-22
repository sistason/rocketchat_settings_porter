#!/bin/python3
from rocketchat_API.rocketchat import RocketChat
from requests.sessions import Session
import os
import json
import time
import logging


logger = logging.getLogger(__name__)


class Porter:
    DEFAULTS_PATH = "default_settings/"

    def __init__(self, user="", password="", host="http://rocketchat:3000", destination="settings.json"):
        self.username = os.environ.get('API_USER', user)
        self.password = os.environ.get('API_PASS', password)
        self.host = os.environ.get('API_HOST', host)
        self.destination = os.environ.get('SETTINGS_PATH', destination)

        self.session = Session()

        self._wait_for_rocketchat()

    def _wait_for_rocketchat(self, rocket=None):
        self.rocket = rocket
        timeout = 60
        logger.info("starting to wait for rocketchat...")
        while timeout:
            time.sleep(1)
            try:
                if self.rocket is None:
                    self.rocket = RocketChat(self.username, self.password, server_url=self.host, session=self.session)
                ret = rocket.info().json()
                if ret.get('success'):
                    logger.info("rocketchat available!")
                    return
            except ConnectionError:
                pass
            except:
                pass
            timeout =- 1
        logger.error("Timeout while waiting for rocketchat!")
        

    def import_settings(self):
        with open(self.destination, 'r') as f:
            settings_to_import = json.load(f)

        logger.info(f"Importing {len(settings_to_import)} settings...")
        self._import(settings_to_import)
        logger.info("Finished importing settings!")

    def _import(self, settings):
        import_oauth = {}

        for _id, value in settings.items():
            if _id.startswith("Accounts_OAuth_Custom-"):
                import_oauth[_id[len("Accounts_OAuth_Custom-"):]] = True
                continue
            self.rocket.settings_update(_id, value)

        if import_oauth:
            # create all neccessary OAuth services
            for i, oauth_service_name in enumerate(import_oauth.keys()):
                logger.debug(f'create {oauth_service_name}')
                json_ = json.dumps({'msg': 'method', 'method': 'addOAuthService', 'params': [oauth_service_name], 'id': 1337+i})
                self.rocket.call_api_post("method.call/addOAuthService", message=json_)

            for _id, value in settings.items():
                if _id.startswith("Accounts_OAuth_Custom-"):
                    self.rocket.settings_update(_id, value)
         

    def _export(self):
        data = self.rocket.settings().json()
        settings = {sett_.get('_id'): sett_.get('value') for sett_ in data.get('settings', [])}
        if not settings:
            logger.error('Nothing returned from server, just "{}"!'.format(data))
            return {}

        api_default_count = settings.get('API_Default_Count', 50)

        # Get remaining
        for call in range(1, int(data.get('total', 1) / api_default_count)+1):
            data = self.rocket.settings(count=api_default_count, offset=call*api_default_count).json()
            for sett_ in data.get('settings', []):
                settings[sett_.get('_id')] =  sett_.get('value')

        return settings

    def export_changed(self):
        logger.info("Exporting all non-default settings...")
        version = self.rocket.info().json().get('info', {}).get('version', 0)
        if not version:
            logger.error('Could not get server version!')
            return

        try:
            with open(os.path.join(self.DEFAULTS_PATH, '{}.json'.format(version)), 'r') as f:
                settings_defaults = json.load(f)
        except FileNotFoundError:
            logger.error('No defaults for version {} found in the directory {}!'.format(version, self.DEFAULTS_PATH))
            return

        settings = self._export()

        settings_updated = {}
        for setting_id, setting_value in settings.items():
            if setting_id not in settings_defaults or setting_value != settings_defaults.get(setting_id):
                settings_updated[setting_id] = setting_value

        with open(self.destination, 'w') as f:
            json.dump(settings_updated, f)
        logger.info(f"Finished exporting {len(settings_updated)} updated settings")

    def export_all(self):
        logger.info("Exporting all settings...")
        settings = self._export()
        with open(self.destination, 'w') as f:
            json.dump(settings, f)
        logger.info(f"Finished exporting {len(settings)} settings")

    def close(self):
        self.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    import sys
    if sys.argv[1] == 'test':
        from tests.settings_porter_tests import test
        sys.exit(0 if test() else 1)

    p = Porter()
    if sys.argv[1] == 'import':
        p.import_settings()
    elif sys.argv[1] == 'export_all':
        p.export_all()
    elif sys.argv[1] == 'export_changed':
        p.export_changed()

    p.close()

