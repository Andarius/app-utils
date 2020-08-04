import requests
import jwt
import time
import json
import argparse
from uuid import uuid4
import pathlib
import pprint
import functools
from typing import Optional

from .utils import CONSOLE

# https://developers.google.com/identity/protocols/oauth2/scopes#androidpublisher
SCOPE = 'https://www.googleapis.com/auth/androidpublisher'
CLIENT_EMAIL = None
PRIVATE_KEY_ID_FROM_JSON = None
PRIVATE_KEY_FROM_JSON = None

URL = 'https://www.googleapis.com/androidpublisher/v3/applications/{PACKAGE_NAME}'
UPLOAD_URL = 'https://www.googleapis.com/upload/androidpublisher/v3/applications/{PACKAGE_NAME}'

TOKEN_FILE = pathlib.Path.home() / '.android_play_api'


def _get_auth_header(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def retry_refresh_token():
    """
    """

    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            for i in range(2):

                resp = func(*args, **kwargs)
                if resp.status_code == 401:
                    session = args[0]
                    token = refresh_token()
                    session.headers.update(_get_auth_header(token))
                else:
                    break
            return resp

        return wrapped

    return wrapper


def _gen_jwt():
    iat = time.time()
    exp = iat + 3600

    payload = {'iss': CLIENT_EMAIL,
               'sub': CLIENT_EMAIL,
               'aud': 'https://oauth2.googleapis.com/token',
               'scope': SCOPE,
               'iat': iat,
               'exp': exp}

    additional_headers = {'kid': PRIVATE_KEY_ID_FROM_JSON}
    signed_jwt = jwt.encode(payload, PRIVATE_KEY_FROM_JSON, headers=additional_headers,
                            algorithm='RS256')
    return signed_jwt


def fetch_access_token(signed_jwt: str) -> str:
    resp = requests.post('https://oauth2.googleapis.com/token', data={
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': signed_jwt
    })
    data = resp.json()
    return data['access_token']


def refresh_token():
    signed_jwt = _gen_jwt()
    token = fetch_access_token(signed_jwt)
    with open(str(TOKEN_FILE), 'w') as f:
        f.write(token)
    print('token: ', token)
    return token


@retry_refresh_token()
def fetch_insert_edit(session, expiry=60 * 10):
    data = {
        'id': str(uuid4()),
        'expiryTimeSeconds': expiry
    }
    resp = session.post(f'{URL}/edits', json=data)
    return resp


@retry_refresh_token()
def fetch_upload_bundle(session: requests.Session,
                        edit_id: str,
                        bundle_path: str):
    resp = session.post(f"{UPLOAD_URL}/edits/{edit_id}/bundles",
                        params={'uploadType': 'media'},
                        headers={'Content-Type': 'application/octet-stream'},
                        data=open(bundle_path, 'rb').read())
    return resp


def upload_bundle(session: requests.Session, path: str, edit_id: str = None):
    if not edit_id:
        resp = fetch_insert_edit(session, 30)
        resp = resp.json()
        edit_id = resp['id']
        CONSOLE.info('Edit created with id ', edit_id)

    CONSOLE.info(f'Starting upload of {path} ...')
    resp = fetch_upload_bundle(session, edit_id, path)
    data = resp.json()
    if resp.status_code != 200:
        CONSOLE.error(data['error']['message'], f' (status: {resp.status_code})')


def _load_config(package_name, config_path) -> Optional[str]:
    global URL, PRIVATE_KEY_FROM_JSON, PRIVATE_KEY_ID_FROM_JSON, CLIENT_EMAIL, UPLOAD_URL
    URL = URL.format(PACKAGE_NAME=package_name)
    UPLOAD_URL = UPLOAD_URL.format(PACKAGE_NAME=package_name)

    if config_path:
        with open(config_path, 'r') as f:
            config = json.load(f)
        PRIVATE_KEY_FROM_JSON = config['private_key']
        PRIVATE_KEY_ID_FROM_JSON = config['private_key_id']
        CLIENT_EMAIL = config['client_email']

    token = None

    if TOKEN_FILE.exists():
        with open(str(TOKEN_FILE), 'r') as f:
            token = f.read()

    return token


def main(options: dict):
    verbose = options.pop('verbose', None)
    func = options.pop('func', None)
    if not func:
        CONSOLE.warn('Nothing to do')
        return
    token = _load_config(options.pop('package'),
                         options.pop('config', None))

    session = requests.Session()
    if token:
        session.headers.update(_get_auth_header(token))

    func(session=session, **options)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Utility for Android play publisher API')
    parser.add_argument('--package',
                        help='Package Name (eg: com.myapp)',
                        required=True)
    parser.add_argument('--config', help='Path to the JSON config file')
    parser.add_argument('-v', '--verbose', action='store_true')
    subparsers = parser.add_subparsers()

    upload_parser = subparsers.add_parser('upload')
    upload_parser.add_argument('--edit-id', type=str, help="""
    Edit ID for the upload, if not specified, a new one will be generated
    """)
    upload_parser.add_argument('-p', '--path', help='Path to the bundle to upload',
                               required=True)
    upload_parser.set_defaults(func=upload_bundle)

    options = parser.parse_args()
    main(vars(options))
