import sys
from pathlib import Path
import json

import httpx
from piou import CommandGroup, Option

from app_utils.logs import logger
from .utils import upload_bundle, Tracks, UploadFailedException, init_token

android = CommandGroup('android')


@android.command('upload')
def run_upload(
        package_name: str = Option(..., '--package',
                                   help='Package Name (eg: com.myapp)'),
        config: str = Option(..., '--config', help='JSON config'),
        edit_id: str | None = Option(None, '--edit-id',
                                     help="Edit ID for the upload, if not specified, a new one will be generated"),
        bundle_path: Path = Option(..., '-p', '--path', help='Path to the bundle to upload'),
        skip_upload: bool = Option(False, '--no-upload', help='Skips the bundle upload'),
        changelog_path: Path = Option(..., '--changelog', help='Path to the CHANGELOG file'),
        track: Tracks = Option(..., '--track', help='Track to upload to')
):
    _config = json.loads(config)
    with httpx.Client() as client:
        init_token(client, package_name, _config)
        try:
            upload_bundle(client, path=bundle_path,
                          changelog=changelog_path,
                          track=track,
                          edit_id=edit_id,
                          skip_upload=skip_upload)
        except UploadFailedException as e:
            logger.error(f'Upload failed. {e.message} (code: {e.status_code})')
            sys.exit(-1)
