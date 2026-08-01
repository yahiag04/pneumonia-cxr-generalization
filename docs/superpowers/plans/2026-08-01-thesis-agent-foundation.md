# Thesis Agent Foundation and CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the standalone `thesis-agent` repository with an installable CLI, validated local project manifests, resumable stage state, recorded human approvals, offline enforcement, and provenance logging.

**Architecture:** Use a Python `src` layout with Typer at the boundary, Pydantic models in the domain, and filesystem repositories behind services. Human-readable YAML/JSONL files are authoritative; atomic JSON files hold resumable execution state. No research connector or LLM provider is implemented in this foundation plan.

**Tech Stack:** Python 3.11+, uv, Typer, Pydantic 2, PyYAML, Rich, pytest, Ruff, mypy, GitHub Actions.

## Global Constraints

- Create a standalone repository at `/Users/yahiaghallale/thesis-agent`; do not add application code to `pneumonia-xray-classifier`.
- Use the package name `thesis-agent`, import package `thesis_agent`, and CLI executable `thesis-agent`.
- Publish under Apache License 2.0.
- Support Python 3.11 and newer on macOS, Linux, and Windows; use only cross-platform `pathlib` and standard-library filesystem operations.
- Keep imported originals immutable; this phase does not import thesis content yet.
- Store project configuration in YAML, approvals and provenance in JSONL, and runtime stage state in JSON.
- An approval must be recorded by the user; non-interactive code must never synthesize one.
- Offline mode must reject network-dependent operations before an adapter is called.
- Use test-driven development: observe every focused test fail before adding its implementation.
- Commit only files belonging to the new repository. Preserve the existing dirty worktree in `pneumonia-xray-classifier`.

## Scope decomposition

This is the first independently testable plan in the approved product design. Subsequent plans will cover, in order:

1. document import and scholarly/web source acquisition;
2. normalization, claims, evidence, and provenance links;
3. LLM/Ollama providers, outline generation, and cited drafting;
4. audit, Markdown/LaTeX/BibTeX/DOCX export, disciplinary profiles, and public release.

The foundation is complete when a user can install the package, initialize a project, inspect its state, move a stage to approval, record a human approval tied to an artifact hash, resume from disk, and prove that offline policy blocks network work.

## Target file map

```text
/Users/yahiaghallale/thesis-agent/
├── .github/workflows/ci.yml
├── .gitignore
├── .python-version
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── docs/design.md
├── pyproject.toml
├── uv.lock
├── src/thesis_agent/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── errors.py
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── approve.py
│   │   ├── init.py
│   │   └── status.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── approvals.py
│   │   ├── config.py
│   │   ├── provenance.py
│   │   └── stages.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── approval_service.py
│   │   ├── network_policy.py
│   │   ├── project_service.py
│   │   └── stage_service.py
│   └── storage/
│       ├── __init__.py
│       ├── atomic.py
│       ├── project_files.py
│       ├── run_log.py
│       └── state_files.py
└── tests/
    ├── conftest.py
    ├── test_approvals.py
    ├── test_cli_init.py
    ├── test_cli_smoke.py
    ├── test_config_repository.py
    ├── test_foundation_acceptance.py
    ├── test_network_policy.py
    ├── test_provenance.py
    └── test_stages.py
```

Each module has one responsibility: `domain` defines validated values without I/O, `storage` serializes them, `services` applies use-case rules, and `commands` translates CLI input and errors.

---

### Task 1: Standalone repository and installable CLI shell

**Files:**
- Create: `/Users/yahiaghallale/thesis-agent/.gitignore`
- Create: `/Users/yahiaghallale/thesis-agent/.python-version`
- Create: `/Users/yahiaghallale/thesis-agent/LICENSE`
- Create: `/Users/yahiaghallale/thesis-agent/README.md`
- Create: `/Users/yahiaghallale/thesis-agent/docs/design.md`
- Create: `/Users/yahiaghallale/thesis-agent/pyproject.toml`
- Create: `/Users/yahiaghallale/thesis-agent/src/thesis_agent/__init__.py`
- Create: `/Users/yahiaghallale/thesis-agent/src/thesis_agent/__main__.py`
- Create: `/Users/yahiaghallale/thesis-agent/src/thesis_agent/cli.py`
- Create: `/Users/yahiaghallale/thesis-agent/tests/test_cli_smoke.py`

**Interfaces:**
- Consumes: approved design at `/Users/yahiaghallale/pneumonia-xray-classifier/docs/superpowers/specs/2026-08-01-thesis-agent-design.md`.
- Produces: `thesis_agent.cli:app`, the `thesis-agent` console script, and package version `0.1.0`.

- [ ] **Step 1: Create the empty repository and copy the approved design**

Run:

```bash
mkdir -p /Users/yahiaghallale/thesis-agent/docs
git -C /Users/yahiaghallale/thesis-agent init
cp -p /Users/yahiaghallale/pneumonia-xray-classifier/docs/superpowers/specs/2026-08-01-thesis-agent-design.md /Users/yahiaghallale/thesis-agent/docs/design.md
```

Expected: a new Git repository exists and `docs/design.md` is byte-identical to the approved specification.

- [ ] **Step 2: Write the failing CLI smoke tests**

Create `tests/test_cli_smoke.py`:

```python
from typer.testing import CliRunner

from thesis_agent.cli import app

runner = CliRunner()


def test_help_names_the_product() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Evidence-first research for university theses" in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == "thesis-agent 0.1.0"
```

- [ ] **Step 3: Run the tests and verify the import failure**

Run: `uv run pytest tests/test_cli_smoke.py -q`

Expected: FAIL because `thesis_agent.cli` does not exist.

- [ ] **Step 4: Create package metadata and the minimal CLI**

Create `pyproject.toml` with these exact project settings:

```toml
[project]
name = "thesis-agent"
version = "0.1.0"
description = "Evidence-first research for university theses"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.11"
dependencies = [
  "pydantic>=2.12,<3",
  "PyYAML>=6,<7",
  "rich>=14,<15",
  "typer>=0.21,<1",
]

[project.scripts]
thesis-agent = "thesis_agent.cli:app"

[dependency-groups]
dev = [
  "mypy>=1.16,<2",
  "pytest>=8.4,<10",
  "ruff>=0.12,<1",
]

[build-system]
requires = ["uv_build>=0.8.14,<0.9.0"]
build-backend = "uv_build"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.11"
strict = true
packages = ["thesis_agent"]
```

Create `src/thesis_agent/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `src/thesis_agent/cli.py`:

```python
import typer

from thesis_agent import __version__

app = typer.Typer(
    name="thesis-agent",
    help="Evidence-first research for university theses",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"thesis-agent {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the installed version.",
    ),
) -> None:
    """Evidence-first research for university theses."""
```

Create `src/thesis_agent/__main__.py`:

```python
from thesis_agent.cli import app

app()
```

Use `uv lock` to generate `uv.lock`. Set `.python-version` to `3.11`; ignore `.venv/`, `dist/`, caches, coverage data, and editor files. Add the unmodified Apache 2.0 license text from <https://www.apache.org/licenses/LICENSE-2.0.txt>. Keep `README.md` to the product name, evidence-first promise, and development commands for this task.

Create `.gitignore` with:

```gitignore
.venv/
dist/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.DS_Store
```

- [ ] **Step 5: Run the focused tests**

Run: `uv run pytest tests/test_cli_smoke.py -q`

Expected: `2 passed`.

- [ ] **Step 6: Verify both entry points**

Run: `uv run thesis-agent --version`

Expected: `thesis-agent 0.1.0`.

Run: `uv run python -m thesis_agent --help`

Expected: exit 0 and the product description.

- [ ] **Step 7: Commit the repository shell**

```bash
git add .
git commit -m "chore: initialize thesis-agent CLI"
```

---

### Task 2: Validated project manifest and atomic storage

**Files:**
- Create: `src/thesis_agent/domain/__init__.py`
- Create: `src/thesis_agent/domain/config.py`
- Create: `src/thesis_agent/errors.py`
- Create: `src/thesis_agent/storage/__init__.py`
- Create: `src/thesis_agent/storage/atomic.py`
- Create: `src/thesis_agent/storage/project_files.py`
- Create: `tests/test_config_repository.py`

**Interfaces:**
- Consumes: Pydantic and PyYAML declared in Task 1.
- Produces: `ProjectConfig`, `NetworkMode`, `DisciplineProfile`, `ProviderRoleConfig`, `load_config(path)`, and `save_config(path, config)`.

- [ ] **Step 1: Write failing round-trip and validation tests**

Create `tests/test_config_repository.py`:

```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from thesis_agent.domain.config import (
    DisciplineProfile,
    NetworkMode,
    ProjectConfig,
)
from thesis_agent.storage.project_files import load_config, save_config


def make_config() -> ProjectConfig:
    return ProjectConfig(
        project_id="3cfe8f18-2b42-4419-9014-b6fae9988964",
        title="CNN per radiografie toraciche",
        question="Come generalizzano le CNN tra dataset radiografici?",
        language="it",
        profile=DisciplineProfile.BIOMEDICAL,
        network=NetworkMode.OFFLINE,
        citation_style="ieee",
    )


def test_config_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "project.yaml"
    save_config(path, make_config())
    assert load_config(path) == make_config()
    assert "question:" in path.read_text(encoding="utf-8")


def test_question_must_not_be_blank() -> None:
    payload = make_config().model_dump(mode="json")
    payload["question"] = " "
    with pytest.raises(ValidationError):
        ProjectConfig.model_validate(payload)
```

- [ ] **Step 2: Run the tests and verify missing modules fail**

Run: `uv run pytest tests/test_config_repository.py -q`

Expected: FAIL because the domain and storage modules do not exist.

- [ ] **Step 3: Define manifest types**

Create `src/thesis_agent/domain/config.py`:

```python
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NetworkMode(StrEnum):
    OFFLINE = "offline"
    ONLINE = "online"


class DisciplineProfile(StrEnum):
    STEM = "stem"
    COMPUTER_SCIENCE = "computer-science"
    BIOMEDICAL = "biomedical"


class ProviderRoleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: int = 1
    project_id: UUID
    title: str = Field(min_length=1)
    question: str = Field(min_length=1)
    language: str = Field(pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$")
    profile: DisciplineProfile
    network: NetworkMode
    citation_style: str = Field(min_length=1)
    providers: dict[str, ProviderRoleConfig] = Field(default_factory=dict)

    @field_validator("title", "question", "citation_style")
    @classmethod
    def reject_whitespace(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned
```

Create `src/thesis_agent/errors.py`:

```python
class ThesisAgentError(Exception):
    """Base class for expected thesis-agent failures."""


class ProjectExistsError(ThesisAgentError):
    pass


class ProjectNotFoundError(ThesisAgentError):
    pass


class InvalidTransitionError(ThesisAgentError):
    pass


class ApprovalError(ThesisAgentError):
    pass


class OfflineModeError(ThesisAgentError):
    pass
```

- [ ] **Step 4: Implement atomic YAML persistence**

Create `src/thesis_agent/storage/atomic.py`:

```python
import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
```

Create `src/thesis_agent/storage/project_files.py`:

```python
from pathlib import Path

import yaml

from thesis_agent.domain.config import ProjectConfig
from thesis_agent.storage.atomic import atomic_write_text


def save_config(path: Path, config: ProjectConfig) -> None:
    payload = config.model_dump(mode="json")
    atomic_write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def load_config(path: Path) -> ProjectConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ProjectConfig.model_validate(payload)
```

- [ ] **Step 5: Run focused checks**

Run: `uv run pytest tests/test_config_repository.py -q`

Expected: `2 passed`.

Run: `uv run mypy src/thesis_agent/domain src/thesis_agent/storage`

Expected: success with no issues.

- [ ] **Step 6: Commit the manifest layer**

```bash
git add src/thesis_agent/domain src/thesis_agent/storage src/thesis_agent/errors.py tests/test_config_repository.py
git commit -m "feat: add validated project manifest"
```

---

### Task 3: Project initialization use case and command

**Files:**
- Create: `src/thesis_agent/services/__init__.py`
- Create: `src/thesis_agent/services/project_service.py`
- Create: `src/thesis_agent/commands/__init__.py`
- Create: `src/thesis_agent/commands/init.py`
- Modify: `src/thesis_agent/cli.py`
- Create: `tests/test_cli_init.py`

**Interfaces:**
- Consumes: `ProjectConfig`, `save_config`, and `ProjectExistsError`.
- Produces: `ProjectService.initialize(root, ...) -> ProjectConfig` and CLI command `thesis-agent init PATH`.

- [ ] **Step 1: Write failing CLI initialization tests**

Create `tests/test_cli_init.py`:

```python
from pathlib import Path

from typer.testing import CliRunner

from thesis_agent.cli import app
from thesis_agent.storage.project_files import load_config

runner = CliRunner()


def test_init_creates_expected_layout(tmp_path: Path) -> None:
    project = tmp_path / "my-thesis"
    result = runner.invoke(
        app,
        [
            "init", str(project),
            "--title", "CNN mediche",
            "--question", "Come cambia la generalizzazione?",
            "--language", "it",
            "--profile", "biomedical",
            "--network", "offline",
        ],
    )
    assert result.exit_code == 0
    assert load_config(project / "project.yaml").title == "CNN mediche"
    assert (project / "originals").is_dir()
    assert (project / "sources" / "documents").is_dir()
    assert (project / "evidence").is_dir()
    assert (project / "exports").is_dir()
    assert (project / ".thesis-agent").is_dir()


def test_init_refuses_existing_project(tmp_path: Path) -> None:
    project = tmp_path / "my-thesis"
    args = [
        "init", str(project), "--title", "T", "--question", "Q?",
        "--language", "it", "--profile", "stem", "--network", "offline",
    ]
    assert runner.invoke(app, args).exit_code == 0
    second = runner.invoke(app, args)
    assert second.exit_code == 2
    assert "already contains a thesis-agent project" in second.output
```

- [ ] **Step 2: Run the tests and verify the missing command**

Run: `uv run pytest tests/test_cli_init.py -q`

Expected: FAIL because `init` is not registered.

- [ ] **Step 3: Implement project initialization**

Create `src/thesis_agent/services/project_service.py` with:

```python
from pathlib import Path
from uuid import uuid4

from thesis_agent.domain.config import DisciplineProfile, NetworkMode, ProjectConfig
from thesis_agent.errors import ProjectExistsError, ProjectNotFoundError
from thesis_agent.storage.project_files import load_config, save_config

PROJECT_DIRS = (
    "originals",
    "sources/documents",
    "evidence",
    "exports",
    ".thesis-agent",
)


class ProjectService:
    def initialize(
        self,
        root: Path,
        *,
        title: str,
        question: str,
        language: str,
        profile: DisciplineProfile,
        network: NetworkMode,
        citation_style: str = "ieee",
    ) -> ProjectConfig:
        manifest = root / "project.yaml"
        if manifest.exists():
            raise ProjectExistsError(f"{root} already contains a thesis-agent project")
        config = ProjectConfig(
            project_id=uuid4(),
            title=title,
            question=question,
            language=language,
            profile=profile,
            network=network,
            citation_style=citation_style,
        )
        root.mkdir(parents=True, exist_ok=True)
        for relative in PROJECT_DIRS:
            (root / relative).mkdir(parents=True, exist_ok=True)
        save_config(manifest, config)
        return config

    def open(self, root: Path) -> ProjectConfig:
        manifest = root / "project.yaml"
        if not manifest.is_file():
            raise ProjectNotFoundError(f"No thesis-agent project at {root}")
        return load_config(manifest)
```

Create `commands/init.py` as a thin Typer adapter:

```python
from pathlib import Path

import typer
from pydantic import ValidationError

from thesis_agent.domain.config import DisciplineProfile, NetworkMode
from thesis_agent.errors import ProjectExistsError
from thesis_agent.services.project_service import ProjectService


def init_command(
    path: Path = typer.Argument(..., help="Directory for the thesis project."),
    title: str = typer.Option(..., "--title"),
    question: str = typer.Option(..., "--question"),
    language: str = typer.Option("en", "--language"),
    profile: DisciplineProfile = typer.Option(DisciplineProfile.STEM, "--profile"),
    network: NetworkMode = typer.Option(NetworkMode.OFFLINE, "--network"),
    citation_style: str = typer.Option("ieee", "--citation-style"),
) -> None:
    try:
        ProjectService().initialize(
            path.resolve(),
            title=title,
            question=question,
            language=language,
            profile=profile,
            network=network,
            citation_style=citation_style,
        )
    except (ProjectExistsError, ValidationError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    typer.echo(f"Initialized thesis-agent project at {path.resolve()}")
```

Register it at the bottom of `cli.py`:

```python
from thesis_agent.commands.init import init_command

app.command("init")(init_command)
```

Do not put filesystem logic in the command module.

- [ ] **Step 4: Run the initialization tests**

Run: `uv run pytest tests/test_cli_init.py -q`

Expected: `2 passed`.

- [ ] **Step 5: Run all current tests and static checks**

Run: `uv run pytest -q`

Expected: `6 passed`.

Run: `uv run ruff check .`

Expected: `All checks passed!`.

- [ ] **Step 6: Commit initialization**

```bash
git add src/thesis_agent/commands src/thesis_agent/services src/thesis_agent/cli.py tests/test_cli_init.py
git commit -m "feat: initialize local thesis projects"
```

---

### Task 4: Resumable stage state machine

**Files:**
- Create: `src/thesis_agent/domain/stages.py`
- Create: `src/thesis_agent/storage/state_files.py`
- Create: `src/thesis_agent/services/stage_service.py`
- Modify: `src/thesis_agent/services/project_service.py`
- Create: `tests/test_stages.py`

**Interfaces:**
- Consumes: project root created by `ProjectService.initialize` and `atomic_write_text`.
- Produces: `Stage`, `StageStatus`, `PipelineState`, `StageService.start`, `StageService.finish`, `StageService.fail`, and `StageService.approve`.

- [ ] **Step 1: Write failing state transition tests**

Create `tests/test_stages.py`:

```python
from pathlib import Path

import pytest

from thesis_agent.domain.stages import Stage, StageStatus
from thesis_agent.errors import InvalidTransitionError
from thesis_agent.services.stage_service import StageService
from thesis_agent.storage.state_files import create_initial_state, save_state


def service(tmp_path: Path) -> StageService:
    state = create_initial_state()
    path = tmp_path / "state.json"
    save_state(path, state)
    return StageService(path)


def test_first_stage_is_ready_and_later_stages_are_locked(tmp_path: Path) -> None:
    current = service(tmp_path).current()
    assert current.stages[Stage.RESEARCH].status == StageStatus.READY
    assert current.stages[Stage.EVIDENCE].status == StageStatus.LOCKED


def test_finish_requires_human_approval_before_unlocking_next_stage(tmp_path: Path) -> None:
    stages = service(tmp_path)
    stages.start(Stage.RESEARCH)
    stages.finish(Stage.RESEARCH, artifact_hash="abc123")
    assert stages.current().stages[Stage.RESEARCH].status == StageStatus.AWAITING_APPROVAL
    stages.approve(Stage.RESEARCH, artifact_hash="abc123")
    current = stages.current()
    assert current.stages[Stage.RESEARCH].status == StageStatus.APPROVED
    assert current.stages[Stage.EVIDENCE].status == StageStatus.READY


def test_locked_stage_cannot_start(tmp_path: Path) -> None:
    with pytest.raises(InvalidTransitionError):
        service(tmp_path).start(Stage.DRAFT)
```

- [ ] **Step 2: Run the tests and verify missing state types**

Run: `uv run pytest tests/test_stages.py -q`

Expected: FAIL because `domain.stages` does not exist.

- [ ] **Step 3: Define the state model**

Create `src/thesis_agent/domain/stages.py`:

```python
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Stage(StrEnum):
    RESEARCH = "research"
    EVIDENCE = "evidence"
    OUTLINE = "outline"
    DRAFT = "draft"
    AUDIT = "audit"
    EXPORT = "export"


STAGE_ORDER = tuple(Stage)


class StageStatus(StrEnum):
    LOCKED = "locked"
    READY = "ready"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    FAILED = "failed"


class StageState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: StageStatus
    artifact_hash: str | None = None
    error: str | None = None


class PipelineState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    stages: dict[Stage, StageState]
```

Create `src/thesis_agent/storage/state_files.py`:

```python
from pathlib import Path

from thesis_agent.domain.stages import PipelineState, Stage, StageState, StageStatus
from thesis_agent.storage.atomic import atomic_write_text


def create_initial_state() -> PipelineState:
    return PipelineState(
        stages={
            stage: StageState(
                status=StageStatus.READY if stage is Stage.RESEARCH else StageStatus.LOCKED
            )
            for stage in Stage
        }
    )


def load_state(path: Path) -> PipelineState:
    return PipelineState.model_validate_json(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: PipelineState) -> None:
    atomic_write_text(path, state.model_dump_json(indent=2) + "\n")
```

- [ ] **Step 4: Implement guarded transitions**

`StageService` must enforce this exact transition table:

```text
ready -> running
running -> awaiting_approval
running -> failed
failed -> running
awaiting_approval -> approved, only when the approved hash matches
approved -> ready is forbidden
locked -> any transition is forbidden
```

Create `src/thesis_agent/services/stage_service.py`:

```python
from pathlib import Path

from thesis_agent.domain.stages import STAGE_ORDER, PipelineState, Stage, StageStatus
from thesis_agent.errors import InvalidTransitionError
from thesis_agent.storage.state_files import load_state, save_state


class StageService:
    def __init__(self, state_path: Path) -> None:
        self._state_path = state_path

    def current(self) -> PipelineState:
        return load_state(self._state_path)

    def start(self, stage: Stage) -> None:
        state = self.current()
        item = state.stages[stage]
        if item.status not in {StageStatus.READY, StageStatus.FAILED}:
            self._invalid(stage, item.status, "running")
        item.status = StageStatus.RUNNING
        item.artifact_hash = None
        item.error = None
        save_state(self._state_path, state)

    def finish(self, stage: Stage, *, artifact_hash: str) -> None:
        state = self.current()
        item = state.stages[stage]
        if item.status is not StageStatus.RUNNING:
            self._invalid(stage, item.status, "awaiting_approval")
        if not artifact_hash:
            raise InvalidTransitionError("artifact hash must not be empty")
        item.status = StageStatus.AWAITING_APPROVAL
        item.artifact_hash = artifact_hash
        save_state(self._state_path, state)

    def fail(self, stage: Stage, *, error: str) -> None:
        state = self.current()
        item = state.stages[stage]
        if item.status is not StageStatus.RUNNING:
            self._invalid(stage, item.status, "failed")
        item.status = StageStatus.FAILED
        item.error = error
        save_state(self._state_path, state)

    def approve(self, stage: Stage, *, artifact_hash: str) -> None:
        state = self.current()
        item = state.stages[stage]
        if item.status is not StageStatus.AWAITING_APPROVAL:
            self._invalid(stage, item.status, "approved")
        if item.artifact_hash != artifact_hash:
            raise InvalidTransitionError("approval hash does not match stage artifact")
        item.status = StageStatus.APPROVED
        position = STAGE_ORDER.index(stage)
        if position + 1 < len(STAGE_ORDER):
            following = state.stages[STAGE_ORDER[position + 1]]
            if following.status is StageStatus.LOCKED:
                following.status = StageStatus.READY
        save_state(self._state_path, state)

    @staticmethod
    def _invalid(stage: Stage, current: StageStatus, requested: str) -> None:
        raise InvalidTransitionError(
            f"cannot move {stage.value} from {current.value} to {requested}"
        )
```

Extend `ProjectService.initialize` to write `.thesis-agent/state.json` using
`create_initial_state()` after all directories are created and before returning.

- [ ] **Step 5: Run focused and full tests**

Run: `uv run pytest tests/test_stages.py tests/test_cli_init.py -q`

Expected: `5 passed`.

Run: `uv run pytest -q`

Expected: all collected tests pass.

- [ ] **Step 6: Commit the state machine**

```bash
git add src/thesis_agent/domain/stages.py src/thesis_agent/storage/state_files.py src/thesis_agent/services/stage_service.py src/thesis_agent/services/project_service.py tests/test_stages.py
git commit -m "feat: add resumable pipeline state"
```

---

### Task 5: Artifact-bound human approvals

**Files:**
- Create: `src/thesis_agent/domain/approvals.py`
- Create: `src/thesis_agent/services/approval_service.py`
- Create: `src/thesis_agent/commands/approve.py`
- Modify: `src/thesis_agent/cli.py`
- Create: `tests/test_approvals.py`

**Interfaces:**
- Consumes: `StageService.approve(stage, artifact_hash)` and an existing artifact path inside the project.
- Produces: `ApprovalRecord`, `sha256_file(path)`, `ApprovalService.approve`, and CLI command `thesis-agent approve STAGE --artifact FILE --by NAME`.

- [ ] **Step 1: Write failing approval tests**

Create `tests/test_approvals.py`:

```python
import json
from pathlib import Path

import pytest

from thesis_agent.domain.stages import Stage
from thesis_agent.errors import ApprovalError
from thesis_agent.services.approval_service import ApprovalService, sha256_file
from thesis_agent.services.stage_service import StageService
from thesis_agent.storage.state_files import create_initial_state, save_state


def prepared_services(tmp_path: Path) -> tuple[ApprovalService, StageService, Path]:
    internal = tmp_path / ".thesis-agent"
    internal.mkdir()
    state_path = internal / "state.json"
    save_state(state_path, create_initial_state())
    stages = StageService(state_path)
    artifact = tmp_path / "sources" / "records.jsonl"
    artifact.parent.mkdir()
    artifact.write_text('{"source_id":"s1"}\n', encoding="utf-8")
    stages.start(Stage.RESEARCH)
    stages.finish(Stage.RESEARCH, artifact_hash=sha256_file(artifact))
    return ApprovalService(tmp_path, stages), stages, artifact


def test_approval_is_appended_and_unlocks_next_stage(tmp_path: Path) -> None:
    approvals, stages, artifact = prepared_services(tmp_path)
    record = approvals.approve(Stage.RESEARCH, artifact, approved_by="student")
    line = (tmp_path / ".thesis-agent" / "approvals.jsonl").read_text().strip()
    assert json.loads(line)["artifact_sha256"] == record.artifact_sha256
    assert stages.current().stages[Stage.EVIDENCE].status.value == "ready"


def test_changed_artifact_cannot_be_approved(tmp_path: Path) -> None:
    approvals, _, artifact = prepared_services(tmp_path)
    artifact.write_text("changed", encoding="utf-8")
    with pytest.raises(ApprovalError, match="artifact has changed"):
        approvals.approve(Stage.RESEARCH, artifact, approved_by="student")
```

- [ ] **Step 2: Run the tests and verify missing approval service**

Run: `uv run pytest tests/test_approvals.py -q`

Expected: FAIL because `approval_service` does not exist.

- [ ] **Step 3: Implement approval records and hashing**

Create `domain/approvals.py`:

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from thesis_agent.domain.stages import Stage


class ApprovalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    stage: Stage
    artifact: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    approved_by: str = Field(min_length=1)
    approved_at: datetime
    notes: str | None = None
```

`sha256_file` must stream the file in 1 MiB chunks. `ApprovalService.approve` resolves both project and artifact paths, rejects artifacts outside the project, compares the current SHA-256 with the hash stored in `StageState`, appends one JSON line to `.thesis-agent/approvals.jsonl`, and only then calls `StageService.approve`. If state persistence fails, truncate the appended line so approval and stage state remain consistent.

Create `src/thesis_agent/services/approval_service.py` with this core:

```python
import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path

from thesis_agent.domain.approvals import ApprovalRecord
from thesis_agent.domain.stages import Stage, StageStatus
from thesis_agent.errors import ApprovalError
from thesis_agent.services.stage_service import StageService


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ApprovalService:
    def __init__(self, project_root: Path, stages: StageService) -> None:
        self._root = project_root.resolve()
        self._stages = stages
        self._log = self._root / ".thesis-agent" / "approvals.jsonl"

    def approve(
        self,
        stage: Stage,
        artifact: Path,
        *,
        approved_by: str,
        notes: str | None = None,
    ) -> ApprovalRecord:
        resolved = artifact.resolve(strict=True)
        try:
            relative = resolved.relative_to(self._root)
        except ValueError as error:
            raise ApprovalError("artifact must be inside the project") from error

        item = self._stages.current().stages[stage]
        if item.status is not StageStatus.AWAITING_APPROVAL:
            raise ApprovalError(f"{stage.value} is not awaiting approval")
        current_hash = sha256_file(resolved)
        if current_hash != item.artifact_hash:
            raise ApprovalError("artifact has changed since the stage finished")

        record = ApprovalRecord(
            stage=stage,
            artifact=relative.as_posix(),
            artifact_sha256=current_hash,
            approved_by=approved_by.strip(),
            approved_at=datetime.now(UTC),
            notes=notes,
        )
        self._log.parent.mkdir(parents=True, exist_ok=True)
        with self._log.open("a+", encoding="utf-8", newline="\n") as handle:
            handle.seek(0, os.SEEK_END)
            rollback_offset = handle.tell()
            handle.write(record.model_dump_json() + "\n")
            handle.flush()
            os.fsync(handle.fileno())
            try:
                self._stages.approve(stage, artifact_hash=current_hash)
            except Exception:
                handle.seek(rollback_offset)
                handle.truncate()
                handle.flush()
                os.fsync(handle.fileno())
                raise
        return record
```

- [ ] **Step 4: Add the explicit CLI approval command**

Create `commands/approve.py`:

```python
from pathlib import Path

import typer

from thesis_agent.domain.stages import Stage
from thesis_agent.errors import ApprovalError, InvalidTransitionError
from thesis_agent.services.approval_service import ApprovalService
from thesis_agent.services.stage_service import StageService


def approve_command(
    stage: Stage = typer.Argument(...),
    project: Path = typer.Option(Path("."), "--project"),
    artifact: Path = typer.Option(..., "--artifact"),
    approved_by: str = typer.Option(..., "--by"),
    notes: str | None = typer.Option(None, "--notes"),
) -> None:
    root = project.resolve()
    stages = StageService(root / ".thesis-agent" / "state.json")
    try:
        record = ApprovalService(root, stages).approve(
            stage,
            artifact,
            approved_by=approved_by,
            notes=notes,
        )
    except (ApprovalError, InvalidTransitionError, FileNotFoundError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    typer.echo(f"Approved {stage.value} at {record.artifact_sha256[:12]}")
```

Register it with `app.command("approve")(approve_command)` in `cli.py`. The
command must never default `--by`, accept `--yes`, or infer approval from a
successful run.

- [ ] **Step 5: Run focused tests and add one CLI invocation test**

Run: `uv run pytest tests/test_approvals.py -q`

Expected: `2 passed`.

Add a CLI test that prepares an awaiting-approval project, invokes `approve`, and asserts the output contains the stage and first 12 characters of the hash. Run the file again and expect `3 passed`.

- [ ] **Step 6: Commit human approvals**

```bash
git add src/thesis_agent/domain/approvals.py src/thesis_agent/services/approval_service.py src/thesis_agent/commands/approve.py src/thesis_agent/cli.py tests/test_approvals.py
git commit -m "feat: record artifact-bound approvals"
```

---

### Task 6: Offline enforcement, provenance log, and status command

**Files:**
- Create: `src/thesis_agent/domain/provenance.py`
- Create: `src/thesis_agent/services/network_policy.py`
- Create: `src/thesis_agent/storage/run_log.py`
- Create: `src/thesis_agent/commands/status.py`
- Modify: `src/thesis_agent/cli.py`
- Create: `tests/test_network_policy.py`
- Create: `tests/test_provenance.py`

**Interfaces:**
- Consumes: `ProjectConfig.network`, `PipelineState`, and `atomic_write_text`.
- Produces: `NetworkPolicy.require_online`, `RunRecord`, `append_run_record`, and CLI command `thesis-agent status --project PATH`.

- [ ] **Step 1: Write the failing offline policy tests**

Create `tests/test_network_policy.py`:

```python
import pytest

from thesis_agent.domain.config import NetworkMode
from thesis_agent.errors import OfflineModeError
from thesis_agent.services.network_policy import NetworkPolicy


def test_offline_mode_blocks_network_operation() -> None:
    policy = NetworkPolicy(NetworkMode.OFFLINE)
    with pytest.raises(OfflineModeError, match="Crossref search requires online mode"):
        policy.require_online("Crossref search")


def test_online_mode_allows_network_operation() -> None:
    NetworkPolicy(NetworkMode.ONLINE).require_online("Crossref search")
```

Create `tests/test_provenance.py`:

```python
import json
from datetime import UTC, datetime
from pathlib import Path

from thesis_agent.domain.provenance import RunRecord, RunStatus
from thesis_agent.storage.run_log import append_run_record


def test_run_record_is_one_json_line_without_secret_values(tmp_path: Path) -> None:
    path = tmp_path / "runs.jsonl"
    record = RunRecord(
        run_id="8c53a8df-490e-4264-a097-f102376cf9d7",
        command="status",
        started_at=datetime(2026, 8, 1, tzinfo=UTC),
        finished_at=datetime(2026, 8, 1, tzinfo=UTC),
        status=RunStatus.SUCCEEDED,
        network_mode="offline",
        input_hashes={},
        output_hashes={},
    )
    append_run_record(path, record)
    payload = json.loads(path.read_text().strip())
    assert payload["command"] == "status"
    assert "api_key" not in payload
```

- [ ] **Step 2: Run the tests and verify missing modules**

Run: `uv run pytest tests/test_network_policy.py tests/test_provenance.py -q`

Expected: FAIL because the policy and provenance modules do not exist.

- [ ] **Step 3: Implement the network gate**

Create `services/network_policy.py`:

```python
from thesis_agent.domain.config import NetworkMode
from thesis_agent.errors import OfflineModeError


class NetworkPolicy:
    def __init__(self, mode: NetworkMode) -> None:
        self._mode = mode

    def require_online(self, operation: str) -> None:
        if self._mode is NetworkMode.OFFLINE:
            raise OfflineModeError(f"{operation} requires online mode")
```

All future source and cloud-provider adapters must receive a `NetworkPolicy` and call `require_online` before opening a socket. They must not inspect configuration directly.

- [ ] **Step 4: Implement structured provenance append**

Create `domain/provenance.py`:

```python
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from thesis_agent.domain.config import NetworkMode


class RunStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class RunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: UUID
    command: str
    started_at: datetime
    finished_at: datetime | None
    status: RunStatus
    network_mode: NetworkMode
    input_hashes: dict[str, str]
    output_hashes: dict[str, str]
    error_type: str | None = None

    @field_validator("started_at", "finished_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        return value
```

Create `storage/run_log.py`:

```python
import os
from pathlib import Path
from threading import Lock

from thesis_agent.domain.provenance import RunRecord

_RUN_LOG_LOCK = Lock()


def append_run_record(path: Path, record: RunRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = record.model_dump_json() + "\n"
    with _RUN_LOG_LOCK, path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
```

- [ ] **Step 5: Add the status command**

Create `commands/status.py`:

```python
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from thesis_agent.domain.provenance import RunRecord, RunStatus
from thesis_agent.domain.stages import Stage
from thesis_agent.errors import ProjectNotFoundError
from thesis_agent.services.approval_service import sha256_file
from thesis_agent.services.project_service import ProjectService
from thesis_agent.services.stage_service import StageService
from thesis_agent.storage.run_log import append_run_record


def status_command(
    project: Path = typer.Option(Path("."), "--project"),
) -> None:
    root = project.resolve()
    started_at = datetime.now(UTC)
    state_path = root / ".thesis-agent" / "state.json"
    try:
        config = ProjectService().open(root)
        state = StageService(state_path).current()
    except (ProjectNotFoundError, ValidationError, OSError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error

    typer.echo(f"{config.title} [{config.network.value}]")
    table = Table("Stage", "Status", "Artifact")
    for stage in Stage:
        item = state.stages[stage]
        table.add_row(stage.value, item.status.value, (item.artifact_hash or "-")[:12])
    Console().print(table)

    append_run_record(
        root / ".thesis-agent" / "runs.jsonl",
        RunRecord(
            run_id=uuid4(),
            command="status",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status=RunStatus.SUCCEEDED,
            network_mode=config.network,
            input_hashes={
                "project.yaml": sha256_file(root / "project.yaml"),
                ".thesis-agent/state.json": sha256_file(state_path),
            },
            output_hashes={},
        ),
    )
```

Register it with `app.command("status")(status_command)` in `cli.py`. Do not log
file content or environment variables.

- [ ] **Step 6: Run tests and manual smoke checks**

Run: `uv run pytest tests/test_network_policy.py tests/test_provenance.py -q`

Expected: `3 passed`.

Run: `uv run thesis-agent status --project /tmp/nonexistent-thesis-agent-project`

Expected: exit 2 and `No thesis-agent project`.

- [ ] **Step 7: Commit policy and observability**

```bash
git add src/thesis_agent/domain/provenance.py src/thesis_agent/services/network_policy.py src/thesis_agent/storage/run_log.py src/thesis_agent/commands/status.py src/thesis_agent/cli.py tests/test_network_policy.py tests/test_provenance.py
git commit -m "feat: enforce offline policy and log runs"
```

---

### Task 7: Documentation, CI, build, and foundation acceptance

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Modify: `README.md`
- Modify: `pyproject.toml`
- Create: `tests/test_foundation_acceptance.py`

**Interfaces:**
- Consumes: all public CLI behavior implemented in Tasks 1-6.
- Produces: documented contributor workflow, cross-version CI, wheel/sdist, and a black-box foundation acceptance test.

- [ ] **Step 1: Write the black-box acceptance test**

Create `tests/test_foundation_acceptance.py`:

```python
from pathlib import Path

from typer.testing import CliRunner

from thesis_agent.cli import app
from thesis_agent.domain.stages import Stage
from thesis_agent.services.approval_service import sha256_file
from thesis_agent.services.stage_service import StageService

runner = CliRunner()


def test_initialize_finish_approve_and_resume(tmp_path: Path) -> None:
    project = tmp_path / "thesis"
    init_result = runner.invoke(
        app,
        [
            "init", str(project), "--title", "Test thesis",
            "--question", "Which evidence supports the claim?",
            "--language", "en", "--profile", "stem", "--network", "offline",
        ],
    )
    assert init_result.exit_code == 0

    artifact = project / "sources" / "records.jsonl"
    artifact.write_text('{"source_id":"source-1"}\n', encoding="utf-8")
    stages = StageService(project / ".thesis-agent" / "state.json")
    stages.start(Stage.RESEARCH)
    stages.finish(Stage.RESEARCH, artifact_hash=sha256_file(artifact))

    approval = runner.invoke(
        app,
        [
            "approve", "research", "--project", str(project),
            "--artifact", str(artifact), "--by", "test-user",
        ],
    )
    assert approval.exit_code == 0

    status = runner.invoke(app, ["status", "--project", str(project)])
    assert status.exit_code == 0
    assert "research" in status.output
    assert "approved" in status.output
    assert "evidence" in status.output
    assert "ready" in status.output
```

- [ ] **Step 2: Run the acceptance test before documentation changes**

Run: `uv run pytest tests/test_foundation_acceptance.py -q`

Expected: PASS if Tasks 1-6 are integrated; otherwise fix the smallest integration defect before proceeding and record it in the Task 6 commit.

- [ ] **Step 3: Document exact user and contributor workflows**

Expand `README.md` with:

- evidence-first and human-approval guarantees;
- installation via `uv tool install .` and editable development via `uv sync`;
- the exact `init`, `status`, and `approve` commands used by the acceptance test;
- project directory tree and offline semantics;
- a roadmap naming the four subsequent phases without claiming those features exist;
- links to `docs/design.md`, `CONTRIBUTING.md`, `SECURITY.md`, and the Apache 2.0 license.

`CONTRIBUTING.md` must require `uv run ruff check .`, `uv run mypy`, and `uv run pytest` before a pull request. `SECURITY.md` must instruct users to report vulnerabilities privately through GitHub Security Advisories, state that imported documents are untrusted, and forbid committing API keys or private thesis material.

- [ ] **Step 4: Add CI**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          python-version: ${{ matrix.python-version }}
          enable-cache: true
      - run: uv sync --locked --all-groups
      - run: uv run ruff check .
      - run: uv run mypy
      - run: uv run pytest -q
      - run: uv build
```

- [ ] **Step 5: Run complete local verification**

Run: `uv sync --locked --all-groups`

Expected: exit 0 without changing `uv.lock`.

Run: `uv run ruff check .`

Expected: `All checks passed!`.

Run: `uv run mypy`

Expected: success with no issues.

Run: `uv run pytest -q`

Expected: all tests pass with zero skipped foundation tests.

Run: `uv build`

Expected: one wheel and one source distribution under `dist/`.

- [ ] **Step 6: Inspect the release artifact**

Create a temporary uv tool environment from the built wheel and run:

```bash
uv tool run --from dist/thesis_agent-0.1.0-py3-none-any.whl thesis-agent --version
```

Expected: `thesis-agent 0.1.0`.

- [ ] **Step 7: Commit the verified foundation**

```bash
git add .github README.md CONTRIBUTING.md SECURITY.md pyproject.toml uv.lock tests/test_foundation_acceptance.py
git commit -m "docs: complete thesis-agent foundation"
```

## Final review checkpoint

Before starting the source-acquisition plan, inspect `git log --oneline`, verify the worktree contains no uncommitted generated files, and rerun the four commands from Task 7 Step 5. Compare the implemented behavior against the foundation acceptance paragraph in this plan and the privacy, approval, and original-immutability requirements in `docs/design.md`.

## Primary documentation used

- uv project and lockfile workflow: <https://docs.astral.sh/uv/guides/projects/>
- Python project entry points: <https://docs.astral.sh/uv/concepts/projects/config/>
- Typer packaging: <https://typer.tiangolo.com/tutorial/package/>
- Typer CLI testing: <https://typer.tiangolo.com/tutorial/testing/>
- pytest temporary paths: <https://docs.pytest.org/en/stable/reference/reference.html#pytest.tmp_path>
