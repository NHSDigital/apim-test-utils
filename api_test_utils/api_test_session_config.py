from dataclasses import dataclass, field
from typing import Optional

import api_test_utils.env


@dataclass(frozen=True)
class APITestSessionConfig:
    base_uri: Optional[str] = field(default_factory=api_test_utils.env.api_base_uri)
    api_environment: Optional[str] = field(default_factory=api_test_utils.env.api_env)
    commit_id: Optional[str] = field(default=api_test_utils.env.source_commit_id)
