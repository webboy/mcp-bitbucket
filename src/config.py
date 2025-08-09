from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BitbucketConfig:
    base_url: str
    token: Optional[str]
    username: Optional[str]
    password: Optional[str]
    default_workspace: Optional[str]


def load_config_from_env() -> BitbucketConfig:
    return BitbucketConfig(
        base_url=os.environ.get("BITBUCKET_URL", "https://api.bitbucket.org/2.0"),
        token=os.environ.get("BITBUCKET_TOKEN"),
        username=os.environ.get("BITBUCKET_USERNAME"),
        password=os.environ.get("BITBUCKET_PASSWORD"),
        default_workspace=os.environ.get("BITBUCKET_WORKSPACE"),
    )


