import sys
from pathlib import Path

import httpx
from piou import CommandGroup, Option

from app_utils.logs import logger
from .utils import upload_bundle, Track, UploadFailedException, init_token

android_group = CommandGroup('android')


@android_group.command('upload')
def run_upload(
        package_name: str = Option(..., '--package',
                                   help='Package Name (eg: com.myapp)'),
        config: Path | None = Option(None, '--config', help='Path to the JSON config file'),
        edit_id: str | None = Option(None, '--edit-id',
                                     help="Edit ID for the upload, if not specified, a new one will be generated"),
        bundle_path: Path = Option(..., '-p', '--path', help='Path to the bundle to upload'),
        skip_upload: bool = Option(False, '--no-upload', help='Skips the bundle upload'),
        changelog_path: Path = Option(..., '--changelog', help='Path to the CHANGELOG file'),
        track: Track = Option(..., '--track', help='Track to upload to'),
        timeout: int = Option(60, '--timeout', help='Fetch timeout')
):
    with httpx.Client(timeout=timeout) as client:
        init_token(client, package_name, config)
        try:
            upload_bundle(client, path=bundle_path,
                          changelog=changelog_path,
                          track=track,
                          edit_id=edit_id,
                          skip_upload=skip_upload)
        except UploadFailedException as e:
            logger.error(f'Upload failed. {e.message} (code: {e.status_code})')
            sys.exit(-1)
