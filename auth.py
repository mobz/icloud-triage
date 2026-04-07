import os
from pyicloud import PyiCloudService
from pyicloud.exceptions import (
    PyiCloudFailedLoginException,
    PyiCloudAPIResponseException,
    PyiCloudAcceptTermsException,
)
import db

COOKIE_DIR = os.path.expanduser("~/Pictures/icloud-triage/app-data/cookies")


class AuthRequired(Exception):
    pass


class TwoFactorRequired(Exception):
    pass


def get_icloud_api():
    creds = db.get_credentials()
    if not creds:
        raise AuthRequired("No credentials stored")

    os.makedirs(COOKIE_DIR, mode=0o700, exist_ok=True)

    try:
        api = PyiCloudService(
            creds["apple_id"],
            creds["password"],
            cookie_directory=COOKIE_DIR,
        )
    except PyiCloudAcceptTermsException:
        raise AuthRequired(
            "Apple requires you to accept updated Terms of Service. "
            "Please sign in at icloud.com, accept the terms, then try again."
        )
    except PyiCloudFailedLoginException as e:
        raise AuthRequired(str(e))

    if api.requires_2fa:
        raise TwoFactorRequired("2FA code required")

    return api
