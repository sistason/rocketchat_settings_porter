#!/bin/python3
from rocketchat_API.rocketchat import RocketChat
from settings_porter import Porter


def create_test_account(host, username, password):
    rocket = RocketChat(server_url=host, ssl_verify=False)
    rocket.users_register(
        email='email@domain.com', name=username, password=password, username=username)
    return rocket


def test():
    username = 'admin'
    password = 'foobarbaz'
    host = 'http://rocketchat:3000'

    rocket = create_test_account(host, username, password)
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
    for setting_id, test_value in test_settings.items():
        result_value = results.get(setting_id)
        if result_value != test_value:
            print('Test LOAD_SETTINGS failed: Settings importet were imported wrongly!')
            print('  Wrong: {}, imported: "{}", exported: "{}"'.format(setting_id, test_value, result_value))

        # restore defaults
        porter._import({setting_id: defaults.get(setting_id)})

    return True


if __name__ == '__main__':
    test()
