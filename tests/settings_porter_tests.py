#!/bin/python3
from rocketchat_API.rocketchat import RocketChat
from rocketchat_API.APIExceptions.RocketExceptions import RocketAuthenticationException
from settings_porter import Porter
import os
import time


def test():
    username = os.environ.get('API_USER', 'admin')
    password = os.environ.get('API_PASS', 'foobarbaz')
    host = os.environ.get('API_HOST', 'http://rocketchat:3000')

    print('Waiting for rocketchat to be fully set up...')
    rocket = RocketChat(server_url=host, ssl_verify=False)

    print('Rocketchat available')

    # If rocketchat-version < 1.0, register the admin-user manually
    if rocket.info().json().get('info', {}).get('version', "-1").startswith('0'):
        rocket.users_register(
            email='email@domain.com', name=username, password=password, username=username)
    try:
        porter = Porter(user=username, password=password, host=host)
    except RocketAuthenticationException:
        # Sometimes the server is up but the admin not yet created. Wait a few secs
        print('first auth failed, wait 5 more secs...')
        time.sleep(5)
        porter = Porter(user=username, password=password, host=host)

    print("Test defaults")
    defaults = porter._export()
    irc_port = defaults.get('IRC_Port')
    if irc_port != 6667:
        print('Test DEFAULTS failed: Default IRC port should be 6667')
        print('Was {}'.format('missing' if irc_port == -1 else irc_port))
        return False

    test_settings = {'API_User_Limit': 5000}

    print("Load testsettings")
    porter._import(test_settings)

    print("Export results")
    results = porter._export()

    print("check results")
    success = True
    for setting_id, test_value in test_settings.items():
        result_value = results.get(setting_id)
        if result_value != test_value:
            print('Test LOAD_SETTINGS failed: Settings importet were imported wrongly!')
            print('  Wrong: {}, imported: "{}", exported: "{}"'.format(setting_id, test_value, result_value))
            success = False

        # restore defaults
        porter._import({setting_id: defaults.get(setting_id)})

    if success:
        print("tests successful!") 
        return True


if __name__ == '__main__':
    test()
