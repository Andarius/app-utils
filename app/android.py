import sys
import requests
import jwt
import time
import json
import argparse
from uuid import uuid4
import pathlib
import functools
from typing import Optional
from enum import Enum
from dataclasses import dataclass
import logging
from .logs import logger, init_logging

from .changelog import parse_markdown, Release as _Release

# https://developers.google.com/identity/protocols/oauth2/scopes#androidpublisher
SCOPE = 'https://www.googleapis.com/auth/androidpublisher'
CLIENT_EMAIL = None
PRIVATE_KEY_ID_FROM_JSON = None
PRIVATE_KEY_FROM_JSON = None

URL = 'https://www.googleapis.com/androidpublisher/v3/applications/{PACKAGE_NAME}'
UPLOAD_URL = 'https://www.googleapis.com/upload/androidpublisher/v3/applications/{PACKAGE_NAME}'
COMMIT_URL = 'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{PACKAGE_NAME}'
TOKEN_FILE = pathlib.Path.home() / '.android_play_api'


class UploadFailedException(Exception):
    def __init__(self, msg: str, status_code: int):
        self.message = msg
        self.status_code = status_code


class Tracks(Enum):
    alpha = 'alpha'
    beta = 'beta'
    internal = 'internal'
    production = 'production'


class Status(Enum):
    unspecified = 'STATUS_UNSPECIFIED'
    draft = 'DRAFT'
    in_progress = 'IN_PROGRESS'
    halted = 'HALTED'
    completed = 'completed'


@dataclass
class Release:
    track: Tracks
    release: _Release
    status: Status = Status.completed

    @property
    def data(self):
        data = {
            "track": self.track.value,
            "releases": [
                {
                    # "name": VERSION_NAME,
                    "versionCodes": self.release.version_code,
                    "userFraction": 1 if self.status != Status.completed else None,
                    "countryTargeting": {
                        "countries": [
                            'France'
                        ],
                        "includeRestOfWorld": False
                    },
                    "releaseNotes": [x.data for x in self.release.release_notes],
                    "status": self.status.value
                }
            ]
        }
        return data


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
    logger.info('Refreshing token...')
    signed_jwt = _gen_jwt()
    token = fetch_access_token(signed_jwt)
    with open(str(TOKEN_FILE), 'w') as f:
        f.write(token)
    logger.info('Token refreshed !')
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


@retry_refresh_token()
def fetch_patch_release(session: requests.Session, edit_id: str, release: Release):
    resp = session.put(f'{URL}/edits/{edit_id}/tracks/{release.track.value}',
                       json=release.data)
    return resp


@retry_refresh_token()
def fetch_commit(session: requests.Session, edit_id: str):
    resp = session.post(f'{COMMIT_URL}/edits/{edit_id}:commit')
    return resp


def upload_bundle(session: requests.Session, path: str,
                  changelog: str,
                  track: str,
                  edit_id: str = None,
                  no_upload: bool = False):
    releases = parse_markdown(changelog)
    track = Tracks[track]
    last_release = releases[0]

    logger.info(f'Starting bundle upload edit (version: {last_release.version}), track: {track.value}')

    if not edit_id:
        resp = fetch_insert_edit(session, 30)
        resp = resp.json()
        edit_id = resp['id']
        logger.info('Edit created with id ', edit_id)

    if not no_upload:
        logger.info(f'Starting upload of {path} ...')
        resp = fetch_upload_bundle(session, edit_id, path)
        data = resp.json()
        if resp.status_code != 200:
            raise UploadFailedException(data['error']['message'], resp.status_code)

        logger.info('Uploaded version: {versionCode}'.format(**data))

    release = Release(track, last_release)
    resp = fetch_patch_release(session, edit_id, release)
    data = resp.json()
    if resp.status_code != 200:
        raise UploadFailedException(data['error']['message'], resp.status_code)

    resp = fetch_commit(session, edit_id)
    data = resp.json()

    if resp.status_code != 200:
        raise UploadFailedException(data['error']['message'], resp.status_code)

    logger.info(f'Release sent ! ({data})')


def _load_config(package_name, config_path) -> Optional[str]:
    global URL, PRIVATE_KEY_FROM_JSON, PRIVATE_KEY_ID_FROM_JSON, CLIENT_EMAIL, UPLOAD_URL, COMMIT_URL
    URL = URL.format(PACKAGE_NAME=package_name)
    UPLOAD_URL = UPLOAD_URL.format(PACKAGE_NAME=package_name)
    COMMIT_URL = COMMIT_URL.format(PACKAGE_NAME=package_name)

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
    func = options.pop('func', None)
    if not func:
        logger.warn('Nothing to do')
        return
    token = _load_config(options.pop('package'),
                         options.pop('config', None))

    session = requests.Session()
    if token:
        session.headers.update(_get_auth_header(token))

    try:
        func(session=session, **options)
    except UploadFailedException as e:
        logger.error(f'Upload failed. {e.message} (code: {e.status_code})')
        sys.exit(-1)


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
    upload_parser.add_argument('--no-upload', action='store_true', help='Skips the bundle upload')
    upload_parser.add_argument('--changelog', help='Path to the CHANGELOG file', required=True)
    upload_parser.add_argument('--track', help='Track to upload to', choices=[x.value for x in Tracks],
                               required=True)
    upload_parser.set_defaults(func=upload_bundle)

    options = parser.parse_args()
    init_logging(log_lvl=logging.INFO if options.verbose else logging.WARNING)
    main(vars(options))
