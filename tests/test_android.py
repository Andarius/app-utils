import shutil

import httpx
from httpx import codes


def test_upload_bundle(tmp_path, static_folder,
                       monkeypatch):

    def fetch_insert_edit_mock(client, expiry):
        return httpx.Response(codes.OK, json={'id': 'new-edit-id'})

    def fetch_upload_bundle(client, edit_id, bundle_path):
        return httpx.Response(codes.OK, json={'versionCode': 1010004})

    def fetch_patch_release_mock(client, edit_id, release):
        return httpx.Response(codes.OK, json={})

    def fetch_commit_mock(client, edit_id):
        return httpx.Response(codes.OK, json={'id': '03436444520213311527', 'expiryTimeSeconds': '1669038863'})

    monkeypatch.setattr('app_utils.jobs.android.utils.fetch_insert_edit',
                        fetch_insert_edit_mock)
    monkeypatch.setattr('app_utils.jobs.android.utils.fetch_upload_bundle',
                        fetch_upload_bundle)
    monkeypatch.setattr('app_utils.jobs.android.utils.fetch_patch_release',
                        fetch_patch_release_mock)
    monkeypatch.setattr('app_utils.jobs.android.utils.fetch_commit',
                        fetch_commit_mock)

    from app_utils.jobs.android.utils import upload_bundle

    shutil.copyfile(static_folder / 'CHANGELOG.md',
                    tmp_path / 'CHANGELOG.md')

    bundle_path = tmp_path
    changelog_path = tmp_path / 'CHANGELOG.md'

    upload_bundle(httpx.Client(),
                  path=bundle_path,
                  changelog=changelog_path,
                  track='internal')
