"""Profile registration and backend access for the REST API."""

from __future__ import annotations

import logging
import typing as t
from contextlib import AsyncExitStack
from urllib.parse import quote

from aiida.common.exceptions import NotExistent
from aiida.manage.configuration import get_config
from aiida.manage.profile_access import ProfileAccessManager
from aiida.orm.implementation import StorageBackend
from fastapi import Request

LOGGER = logging.getLogger('uvicorn')


class ProfileBackendRegistry:
    """Hold one storage backend for each profile enabled in the local API config."""

    def __init__(self, profiles: list[str], cleanup: AsyncExitStack) -> None:
        self._backends: dict[str, StorageBackend] = {}
        config = get_config()

        registered_profiles = config.profile_names
        enabled_profiles = profiles or registered_profiles
        self.default_profile = t.cast(str | None, config.default_profile_name)
        if self.default_profile and self.default_profile not in enabled_profiles:
            enabled_profiles.insert(0, self.default_profile)

        LOGGER.info(f'Connecting to the following profiles: {enabled_profiles}')

        for profile_name in enabled_profiles:
            try:
                profile = config.get_profile(profile_name)
                ProfileAccessManager(profile).request_access()
                backend = profile.storage_cls(profile)
            except Exception:
                LOGGER.error(
                    f'failed to load profile {profile_name}. '
                    f'Check `verdi -p {profile_name} status` for more information.'
                )
                continue
            cleanup.callback(backend.close)
            self._backends[profile_name] = backend

        LOGGER.info(f'Connected profiles: {list(self._backends.keys())}')

    @property
    def profiles(self) -> tuple[str, ...]:
        """Return the profiles enabled for profile-scoped API routes."""
        return tuple(self._backends)

    def get_backend(self, profile_name: str) -> StorageBackend:
        """Return the registered backend for a profile."""
        try:
            return self._backends[profile_name]
        except KeyError as exception:
            msg = f'Profile {profile_name!r} is not available for this REST API.'
            raise NotExistent(msg) from exception


def get_profile_backend(request: Request, profile: str) -> StorageBackend:
    """Resolve and cache the backend named by the required profile path parameter."""
    registry: ProfileBackendRegistry = request.app.state.profile_backends
    backend = getattr(request.state, 'profile_backend', None)
    if backend is not None:
        return backend
    backend = registry.get_backend(profile)
    request.state.profile_backend = backend
    return backend


def get_profile_api_path(request: Request) -> str:
    """Return the API base path for the profile in the current request, if any."""
    api_path = request.app.state.api_path
    profile = request.path_params.get('profile')
    if profile is None:
        return api_path
    return f'{api_path}/profiles/{quote(profile, safe="")}'
