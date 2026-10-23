"""
Unified component registry for Grafana backup v2.

This module is the single source of truth for which components exist, how they
are named, which classes implement their backup/restore, and what order they
must be restored in (dependency ordering).

Adding a new component now requires only one entry here — the coordinators in
``v2/core`` no longer contain long ``if/elif`` chains.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from grafana_backup.v2.components.base import BaseComponent, ComponentConfig
from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


@dataclass(frozen=True)
class ComponentDefinition:
    """Describes a single backup/restore component.

    Attributes:
        name: Canonical component name (dash-separated, matches the v1 registry
            and CLI, e.g. ``"contact-points"``).
        backup_cls: Component class implementing the backup, or ``None`` if the
            component cannot be backed up.
        backup_config_cls: Config class used to instantiate ``backup_cls``.
        restore_cls: Component class implementing the restore, or ``None``.
        restore_config_cls: Config class used to instantiate ``restore_cls``.
        depends_on: Names of components that must be restored *before* this one.
        file_extension: Default file extension used when no config overrides it.
    """

    name: str
    backup_cls: type[BaseComponent] | None = None
    backup_config_cls: type[ComponentConfig] | None = None
    restore_cls: type[BaseRestoreComponent] | None = None
    restore_config_cls: type[RestoreConfig] | None = None
    depends_on: tuple[str, ...] = field(default_factory=tuple)
    file_extension: str = "json"

    @property
    def can_backup(self) -> bool:
        return self.backup_cls is not None and self.backup_config_cls is not None

    @property
    def can_restore(self) -> bool:
        return self.restore_cls is not None and self.restore_config_cls is not None


class ComponentRegistry:
    """Registry holding all component definitions."""

    def __init__(self) -> None:
        self._definitions: dict[str, ComponentDefinition] = {}

    def register(self, definition: ComponentDefinition) -> None:
        if definition.name in self._definitions:
            raise ValueError(f"Component '{definition.name}' is already registered")
        self._definitions[definition.name] = definition

    def get(self, name: str) -> ComponentDefinition | None:
        return self._definitions.get(name)

    def names(self) -> list[str]:
        """Return all registered component names."""
        return list(self._definitions.keys())

    def backup_names(self) -> list[str]:
        """Return names of components that support backup."""
        return [d.name for d in self._definitions.values() if d.can_backup]

    def restore_names(self) -> list[str]:
        """Return component names in a valid restore order (dependency-first)."""
        return self.order_for_restore(list(self._definitions.keys()))

    def order_for_restore(self, names: list[str]) -> list[str]:
        """Topologically sort names so dependencies are restored first.

        Unknown dependencies are ignored (they may be optional). Cycles are
        tolerated: any remaining components are appended in registration order
        so that a misconfigured dependency never hangs the restore.
        """
        requested = [n for n in names if n in self._definitions]
        ordered: list[str] = []
        visited: set[str] = set()
        visiting: set[str] = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                # Cycle detected; break it by returning early.
                return
            visiting.add(name)
            definition = self._definitions.get(name)
            if definition:
                for dep in definition.depends_on:
                    if dep in self._definitions:
                        visit(dep)
            visiting.discard(name)
            visited.add(name)
            ordered.append(name)

        for name in requested:
            visit(name)

        # Append any registered-but-not-requested names only if caller asked for all.
        return ordered

    def build_backup(self, name: str, backup_dir, timestamp: str):
        """Instantiate a component's backup implementation."""
        definition = self._definitions.get(name)
        if (
            definition is None
            or not definition.can_backup
            or definition.backup_cls is None
            or definition.backup_config_cls is None
        ):
            return None
        config = definition.backup_config_cls()
        return definition.backup_cls(config, backup_dir, timestamp)

    def build_restore(self, name: str, backup_dir, timestamp: str):
        """Instantiate a component's restore implementation."""
        definition = self._definitions.get(name)
        if (
            definition is None
            or not definition.can_restore
            or definition.restore_cls is None
            or definition.restore_config_cls is None
        ):
            return None
        config = definition.restore_config_cls()
        return definition.restore_cls(config, backup_dir, timestamp)


def _build_default_registry() -> ComponentRegistry:
    """Build and populate the default component registry.

    Imports are performed lazily inside the function to avoid circular imports
    between ``components/__init__`` and individual component modules.
    """
    from grafana_backup.v2.components.alert_channels import (
        AlertChannelsComponent,
        AlertChannelsConfig,
    )
    from grafana_backup.v2.components.alert_rules import AlertRulesComponent, AlertRulesConfig
    from grafana_backup.v2.components.annotations import AnnotationsComponent, AnnotationsConfig
    from grafana_backup.v2.components.contact_points import (
        ContactPointsComponent,
        ContactPointsConfig,
    )
    from grafana_backup.v2.components.dashboard_versions import (
        DashboardVersionsComponent,
        DashboardVersionsConfig,
    )
    from grafana_backup.v2.components.dashboards import DashboardConfig, DashboardsComponent
    from grafana_backup.v2.components.datasources import DatasourceConfig, DatasourcesComponent
    from grafana_backup.v2.components.folders import FolderConfig, FoldersComponent
    from grafana_backup.v2.components.library_elements import (
        LibraryElementsComponent,
        LibraryElementsConfig,
    )
    from grafana_backup.v2.components.notification_policies import (
        NotificationPoliciesComponent,
        NotificationPoliciesConfig,
    )
    from grafana_backup.v2.components.organizations import (
        OrganizationsComponent,
        OrganizationsConfig,
    )
    from grafana_backup.v2.components.restore_alert_channels import (
        AlertChannelsRestoreComponent,
        AlertChannelsRestoreConfig,
    )
    from grafana_backup.v2.components.restore_alert_rules import (
        AlertRulesRestoreComponent,
        AlertRulesRestoreConfig,
    )
    from grafana_backup.v2.components.restore_annotations import (
        AnnotationsRestoreComponent,
        AnnotationsRestoreConfig,
    )
    from grafana_backup.v2.components.restore_contact_points import (
        ContactPointsRestoreComponent,
        ContactPointsRestoreConfig,
    )
    from grafana_backup.v2.components.restore_dashboard_versions import (
        DashboardVersionsRestoreComponent,
        DashboardVersionsRestoreConfig,
    )
    from grafana_backup.v2.components.restore_dashboards import (
        DashboardsRestoreComponent,
        DashboardsRestoreConfig,
    )
    from grafana_backup.v2.components.restore_datasources import (
        DatasourcesRestoreComponent,
        DatasourcesRestoreConfig,
    )
    from grafana_backup.v2.components.restore_folders import (
        FoldersRestoreComponent,
        FoldersRestoreConfig,
    )
    from grafana_backup.v2.components.restore_library_elements import (
        LibraryElementsRestoreComponent,
        LibraryElementsRestoreConfig,
    )
    from grafana_backup.v2.components.restore_notification_policies import (
        NotificationPoliciesRestoreComponent,
        NotificationPoliciesRestoreConfig,
    )
    from grafana_backup.v2.components.restore_organizations import (
        OrganizationsRestoreComponent,
        OrganizationsRestoreConfig,
    )
    from grafana_backup.v2.components.restore_snapshots import (
        SnapshotsRestoreComponent,
        SnapshotsRestoreConfig,
    )
    from grafana_backup.v2.components.restore_team_members import (
        TeamMembersRestoreComponent,
        TeamMembersRestoreConfig,
    )
    from grafana_backup.v2.components.restore_teams import TeamsRestoreComponent, TeamsRestoreConfig
    from grafana_backup.v2.components.restore_users import UsersRestoreComponent, UsersRestoreConfig
    from grafana_backup.v2.components.snapshots import SnapshotsComponent, SnapshotsConfig
    from grafana_backup.v2.components.team_members import TeamMembersComponent, TeamMembersConfig
    from grafana_backup.v2.components.teams import TeamsComponent, TeamsConfig
    from grafana_backup.v2.components.users import UsersComponent, UsersConfig

    registry = ComponentRegistry()

    # --- Access / identity layer (must exist before folders/dashboards) ---
    registry.register(
        ComponentDefinition(
            name="organizations",
            backup_cls=OrganizationsComponent,
            backup_config_cls=OrganizationsConfig,
            restore_cls=OrganizationsRestoreComponent,
            restore_config_cls=OrganizationsRestoreConfig,
            depends_on=(),
            file_extension="organization",
        )
    )
    registry.register(
        ComponentDefinition(
            name="users",
            backup_cls=UsersComponent,
            backup_config_cls=UsersConfig,
            restore_cls=UsersRestoreComponent,
            restore_config_cls=UsersRestoreConfig,
            depends_on=("organizations",),
            file_extension="user",
        )
    )
    registry.register(
        ComponentDefinition(
            name="teams",
            backup_cls=TeamsComponent,
            backup_config_cls=TeamsConfig,
            restore_cls=TeamsRestoreComponent,
            restore_config_cls=TeamsRestoreConfig,
            depends_on=("organizations",),
            file_extension="team",
        )
    )
    registry.register(
        ComponentDefinition(
            name="team-members",
            backup_cls=TeamMembersComponent,
            backup_config_cls=TeamMembersConfig,
            restore_cls=TeamMembersRestoreComponent,
            restore_config_cls=TeamMembersRestoreConfig,
            depends_on=("teams", "users"),
            file_extension="team_member",
        )
    )

    # --- Core layer ---
    registry.register(
        ComponentDefinition(
            name="folders",
            backup_cls=FoldersComponent,
            backup_config_cls=FolderConfig,
            restore_cls=FoldersRestoreComponent,
            restore_config_cls=FoldersRestoreConfig,
            depends_on=(),
            file_extension="folder",
        )
    )
    registry.register(
        ComponentDefinition(
            name="library-elements",
            backup_cls=LibraryElementsComponent,
            backup_config_cls=LibraryElementsConfig,
            restore_cls=LibraryElementsRestoreComponent,
            restore_config_cls=LibraryElementsRestoreConfig,
            depends_on=("folders",),
            file_extension="library_element",
        )
    )
    registry.register(
        ComponentDefinition(
            name="datasources",
            backup_cls=DatasourcesComponent,
            backup_config_cls=DatasourceConfig,
            restore_cls=DatasourcesRestoreComponent,
            restore_config_cls=DatasourcesRestoreConfig,
            depends_on=(),
            file_extension="datasource",
        )
    )
    registry.register(
        ComponentDefinition(
            name="dashboards",
            backup_cls=DashboardsComponent,
            backup_config_cls=DashboardConfig,
            restore_cls=DashboardsRestoreComponent,
            restore_config_cls=DashboardsRestoreConfig,
            depends_on=("folders", "library-elements", "datasources"),
            file_extension="dashboard",
        )
    )
    registry.register(
        ComponentDefinition(
            name="dashboard-versions",
            backup_cls=DashboardVersionsComponent,
            backup_config_cls=DashboardVersionsConfig,
            restore_cls=DashboardVersionsRestoreComponent,
            restore_config_cls=DashboardVersionsRestoreConfig,
            depends_on=("dashboards",),
            file_extension="dashboard_version",
        )
    )
    registry.register(
        ComponentDefinition(
            name="snapshots",
            backup_cls=SnapshotsComponent,
            backup_config_cls=SnapshotsConfig,
            restore_cls=SnapshotsRestoreComponent,
            restore_config_cls=SnapshotsRestoreConfig,
            depends_on=(),
            file_extension="snapshot",
        )
    )
    registry.register(
        ComponentDefinition(
            name="annotations",
            backup_cls=AnnotationsComponent,
            backup_config_cls=AnnotationsConfig,
            restore_cls=AnnotationsRestoreComponent,
            restore_config_cls=AnnotationsRestoreConfig,
            depends_on=("dashboards",),
            file_extension="annotation",
        )
    )

    # --- Alerting layer ---
    registry.register(
        ComponentDefinition(
            name="alert-channels",
            backup_cls=AlertChannelsComponent,
            backup_config_cls=AlertChannelsConfig,
            restore_cls=AlertChannelsRestoreComponent,
            restore_config_cls=AlertChannelsRestoreConfig,
            depends_on=(),
            file_extension="alert_channel",
        )
    )
    registry.register(
        ComponentDefinition(
            name="alert-rules",
            backup_cls=AlertRulesComponent,
            backup_config_cls=AlertRulesConfig,
            restore_cls=AlertRulesRestoreComponent,
            restore_config_cls=AlertRulesRestoreConfig,
            depends_on=("folders", "datasources"),
            file_extension="alert_rule",
        )
    )
    registry.register(
        ComponentDefinition(
            name="contact-points",
            backup_cls=ContactPointsComponent,
            backup_config_cls=ContactPointsConfig,
            restore_cls=ContactPointsRestoreComponent,
            restore_config_cls=ContactPointsRestoreConfig,
            depends_on=(),
            file_extension="contact_point",
        )
    )
    registry.register(
        ComponentDefinition(
            name="notification-policy",
            backup_cls=NotificationPoliciesComponent,
            backup_config_cls=NotificationPoliciesConfig,
            restore_cls=NotificationPoliciesRestoreComponent,
            restore_config_cls=NotificationPoliciesRestoreConfig,
            depends_on=("contact-points", "alert-rules"),
            file_extension="notification_policy",
        )
    )

    return registry


# Module-level singleton registry used by the coordinators.
REGISTRY = _build_default_registry()
