import functools
import time
from dataclasses import dataclass
from enum import Enum
from json import JSONDecodeError
from pathlib import Path
from typing import Callable, ParamSpec, Concatenate
from uuid import uuid4

import httpx
import jwt
from httpx import codes

from app_utils.jobs.changelog import parse_markdown, Release as _Release
from app_utils.logs import logger

TOKEN_FILE = Path.home() / '.android_play_api'

# https://developers.google.com/identity/protocols/oauth2/scopes#androidpublisher
SCOPE = 'https://www.googleapis.com/auth/androidpublisher'
CLIENT_EMAIL = None
PRIVATE_KEY_ID_FROM_JSON = None
PRIVATE_KEY_FROM_JSON = None

URL = 'https://www.googleapis.com/androidpublisher/v3/applications/{PACKAGE_NAME}'
UPLOAD_URL = 'https://www.googleapis.com/upload/androidpublisher/v3/applications/{PACKAGE_NAME}'
COMMIT_URL = 'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{PACKAGE_NAME}'


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
        country_targeting = {
            "countries": [
                'France'
            ],
            "includeRestOfWorld": False
        } if self.track != self.track.internal else None
        data = {
            "track": self.track.value,
            "releases": [
                {
                    # "name": VERSION_NAME,
                    "versionCodes": self.release.version_code,
                    "userFraction": 1 if self.status != Status.completed else None,
                    "countryTargeting": country_targeting,
                    "releaseNotes": [x.data for x in self.release.release_notes],
                    "status": self.status.value
                }
            ]
        }
        return data


def _get_auth_header(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


P = ParamSpec('P')


def retry_refresh_token():
    """
    """

    def wrapper(func: Callable[Concatenate[httpx.Client, P], httpx.Response]):
        @functools.wraps(func)
        def wrapped(client: httpx.Client, *args: P.args, **kwargs: P.kwargs):
            for i in range(2):
                resp = func(client, *args, **kwargs)
                if resp.status_code == codes.UNAUTHORIZED:
                    token = refresh_token(client)
                    client.headers.update(_get_auth_header(token))
                else:
                    break

            raise NotImplementedError(f'Got no response')

        return wrapped

    return wrapper


def _gen_jwt():
    if not PRIVATE_KEY_FROM_JSON:
        raise ValueError('PRIVATE_KEY_FROM_JSON must be set')

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


def fetch_access_token(client: httpx.Client, signed_jwt: str) -> str:
    resp = client.post('https://oauth2.googleapis.com/token', data={
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': signed_jwt
    })
    data = resp.json()
    return data['access_token']


def refresh_token(client: httpx.Client):
    logger.info('Refreshing token...')
    signed_jwt = _gen_jwt()
    token = fetch_access_token(client, signed_jwt)
    TOKEN_FILE.write_text(token)
    logger.info('Token refreshed !')
    return token


@retry_refresh_token()
def fetch_insert_edit(client: httpx.Client, expiry=60 * 10):
    data = {
        'id': str(uuid4()),
        'expiryTimeSeconds': expiry
    }
    resp = client.post(f'{URL}/edits', json=data)
    return resp


@retry_refresh_token()
def fetch_upload_bundle(session: httpx.Client,
                        edit_id: str,
                        bundle_path: Path):
    resp = session.post(f"{UPLOAD_URL}/edits/{edit_id}/bundles",
                        params={'uploadType': 'media'},
                        headers={'Content-Type': 'application/octet-stream'},
                        content=bundle_path.read_bytes())
    return resp


@retry_refresh_token()
def fetch_patch_release(client: httpx.Client, edit_id: str, release: Release):
    resp = client.put(f'{URL}/edits/{edit_id}/tracks/{release.track.value}',
                      json=release.data)
    return resp


@retry_refresh_token()
def fetch_commit(client: httpx.Client, edit_id: str):
    resp = client.post(f'{COMMIT_URL}/edits/{edit_id}:commit')
    return resp


def upload_bundle(client: httpx.Client,
                  path: Path,
                  changelog: Path,
                  track: Tracks,
                  edit_id: str | None = None,
                  skip_upload: bool = False):
    releases = parse_markdown(changelog)
    last_release = releases[0]

    logger.info(f'Starting bundle upload edit (version: {last_release.version}), track: {track.value}')

    if not edit_id:
        resp = fetch_insert_edit(client, 30)
        resp = resp.json()
        _edit_id = resp['id']
        logger.info('Edit created with id ', _edit_id)
    else:
        _edit_id = edit_id

    if not skip_upload:
        logger.info(f'Starting upload of {path} ...')
        resp = fetch_upload_bundle(client, _edit_id, path)
        data = resp.json()
        if resp.status_code != codes.OK:
            raise UploadFailedException(data['error']['message'], resp.status_code)

        logger.info('Uploaded version: {versionCode}'.format(**data))

    release = Release(track, last_release)
    resp = fetch_patch_release(client, _edit_id, release)
    data = resp.json()
    if resp.status_code != codes.OK:
        raise UploadFailedException(data['error']['message'], resp.status_code)

    resp = fetch_commit(client, _edit_id)
    try:
        data = resp.json()
    except JSONDecodeError:
        logger.error(resp.text)
        raise

    if resp.status_code != codes.OK:
        raise UploadFailedException(data['error']['message'], resp.status_code)

    logger.info(f'Release sent ! ({data})')


def _load_config(package_name: str, config: dict | None = None) -> str | None:
    global URL, PRIVATE_KEY_FROM_JSON, PRIVATE_KEY_ID_FROM_JSON, CLIENT_EMAIL, UPLOAD_URL, COMMIT_URL
    URL = URL.format(PACKAGE_NAME=package_name)
    UPLOAD_URL = UPLOAD_URL.format(PACKAGE_NAME=package_name)
    COMMIT_URL = COMMIT_URL.format(PACKAGE_NAME=package_name)

    if config:
        PRIVATE_KEY_FROM_JSON = config['private_key']
        PRIVATE_KEY_ID_FROM_JSON = config['private_key_id']
        CLIENT_EMAIL = config['client_email']

    token = TOKEN_FILE.read_text() if TOKEN_FILE.exists() else None

    return token


def init_token(client: httpx.Client,
               package: str,
               config: dict | None = None):
    token = _load_config(package, config)
    if token:
        client.headers.update(_get_auth_header(token))
