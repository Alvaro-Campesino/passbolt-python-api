import requests
import configparser
import gnupg
import urllib.parse
import yaml

LOGIN_URL = "/auth/login.json"
VERIFY_URL = "/auth/verify.json"


class PassboltAPI:

    def __init__(self, config_path, new_keys=False, delete_old_keys=False):
        """
        :param config_path: Path to the config file.
        :param delete_old_keys: Set true if old keys need to be deleted
        """
        self.requests_session = requests.Session()
        self.config = configparser.ConfigParser()
        self.config.read_file(open(config_path, "r"))

        if not self.config["PASSBOLT"]["SERVER"]:
            raise ValueError("Missing value for SERVER in config.ini")

        self.server_url = self.config["PASSBOLT"]["SERVER"]
        self.user_fingerprint = self.config["PASSBOLT"]["USER_FINGERPRINT"]
        self.gpg = gnupg.GPG()
        if delete_old_keys:
            self._delete_old_keys()
        if new_keys:
            self._import_gpg_keys()
        try:
            self.gpg_fingerprint = [
                i for i in self.gpg.list_keys() if i["fingerprint"] == self.config["PASSBOLT"]["USER_FINGERPRINT"]
            ][0]["fingerprint"]
        except IndexError:
            raise Exception("GPG public key could not be found. Check: gpg --list-keys")

        if self.config["PASSBOLT"]["USER_FINGERPRINT"] not in [i["fingerprint"] for i in self.gpg.list_keys(True)]:
            raise Exception("GPG private key could not be found. Check: gpg --list-secret-keys")
        self._login()

    def urls_vars(self, resource_id='', user_id='', group_id='' ):
        """This is a dictionary object containing the endpoints from the swagger
        it makes easier to update them if there are changes in the """
        { 'resources' : '/resources.json',
          'single_resource' : '/resources/{}.json?api-version=v2'.format(resource_id),
          'users' : '/users.json?api-version=v2',
          'single_user' : '/users/{}.json?api-version=v2'.format(user_id),
          'check_user_modifiable' : '/users/{}/dry-run?api-version=v2'.format(user_id),
          'groups'  : '/groups.json?api-version=v2',
          'single_group' : '/groups/{}.json?api-version=v2'.format(group_id),
          'check_group_modifiable' : '/groups/{}/dry-run?api-version=v2'.format(group_id),
          'sharable_users_and_groups' : '/share/search-aros.json?api-version=v2'
          'password_share'



          }
        with open('swagger.yaml', 'r')


    def __enter__(self):
        return self

    def __del__(self):
        self.close_session()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_session()

    def _delete_old_keys(self):
        for i in self.gpg.list_keys():
            self.gpg.delete_keys(i["fingerprint"], True, passphrase="")
            self.gpg.delete_keys(i["fingerprint"], False)

    def _import_gpg_keys(self):
        #if not self.config["PASSBOLT"]["USER_PUBLIC_KEY_FILE"]:
        #    raise ValueError("Missing value for USER_PUBLIC_KEY_FILE in config.ini")
        if not self.config["PASSBOLT"]["USER_PRIVATE_KEY_FILE"]:
            raise ValueError("Missing value for USER_PRIVATE_KEY_FILE in config.ini")
        self.gpg.import_keys(open(self.config["PASSBOLT"]["USER_PUBLIC_KEY_FILE"], "r").read())
        self.gpg.import_keys(open(self.config["PASSBOLT"]["USER_PRIVATE_KEY_FILE"], "r").read())

    def _login(self):
        r = self.requests_session.post(self.server_url + LOGIN_URL, json={
            "gpg_auth": {"keyid": self.gpg_fingerprint}})
        encrypted_token = r.headers["X-GPGAuth-User-Auth-Token"]
        encrypted_token = urllib.parse.unquote(encrypted_token)
        encrypted_token = encrypted_token.replace("\+", " ")
        token = self.decrypt(encrypted_token)
        self.requests_session.post(self.server_url + LOGIN_URL, json={
            "gpg_auth": {
                "keyid": self.gpg_fingerprint,
                "user_token_result": token
            },
        })

    def encrypt(self, text):
        return str(self.gpg.encrypt(
            data=text,
            recipients=self.gpg_fingerprint,
            always_trust=True
        ))

    def decrypt(self, text):
        return str(self.gpg.decrypt(
            text,
            always_trust=True,
            passphrase=str(self.config["PASSBOLT"]["PASSPHRASE"])
        ))

    def get_server_public_key(self):
        r = self.requests_session.get(self.server_url + VERIFY_URL)
        return r.json()["body"]["fingerprint"], r.json()["body"]["keydata"]

    def get(self, url):
        r = self.requests_session.get(self.server_url + url)
        return r.json()

    def post(self, url, data):
        r = self.requests_session.post(self.server_url + url, json=data)
        return r.json()

    def put(self, url, data):
        r = self.requests_session.put(self.server_url + url, json=data)
        return r.json()

    def delete(self, url):
        r = self.requests_session.delete(self.server_url + url)
        return r.json()

    def close_session(self):
        self.requests_session.close()

    def get_all_keys_resources(self):
        r = self.get(self, )



