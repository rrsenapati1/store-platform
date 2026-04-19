import type {
  ControlPlaneObservabilitySummary,
  ControlPlanePlatformTenantRecord,
  ControlPlaneSystemEnvironmentContract,
  ControlPlaneSystemSecurityControls,
  ControlPlaneTenantLifecycleSummary,
} from '@store/types';

export type PlatformAdminSection =
  | 'overview'
  | 'release'
  | 'operations'
  | 'tenants'
  | 'commercial'
  | 'settings';

export type PlatformTone = 'neutral' | 'warning' | 'success' | 'danger';

export type PlatformSignal = {
  label: string;
  value: string;
  tone?: PlatformTone;
};

export type PlatformException = {
  id: string;
  title: string;
  detail: string;
  tone?: PlatformTone;
};

export type PlatformDetailItem = {
  label: string;
  value: string;
  tone?: PlatformTone;
};

export type PlatformAdminOverviewModel = {
  commandContext: {
    environmentLabel: string;
    releaseLabel: string;
    healthLabel: string;
    healthTone: PlatformTone;
  };
  postureSignals: PlatformSignal[];
  criticalExceptions: PlatformException[];
  tenantExceptions: PlatformException[];
  runtimeHighlights: PlatformDetailItem[];
  releaseHighlights: PlatformDetailItem[];
};

function resolveReleaseHealthTone(
  observabilitySummary: ControlPlaneObservabilitySummary | null,
  securityControls: ControlPlaneSystemSecurityControls | null,
  environmentContract: ControlPlaneSystemEnvironmentContract | null,
): PlatformTone {
  if (!observabilitySummary || !securityControls || !environmentContract) {
    return 'warning';
  }
  if (
    observabilitySummary.operations.dead_letter_count > 0
    || observabilitySummary.runtime.degraded_branch_count > 0
    || observabilitySummary.backup.status !== 'ok'
    || !securityControls.secure_headers_enabled
    || !securityControls.secure_headers_hsts_enabled
  ) {
    return 'danger';
  }
  return observabilitySummary.system_health.status === 'ok' ? 'success' : 'warning';
}

function summarizeSecurityTone(
  securityControls: ControlPlaneSystemSecurityControls | null,
): PlatformTone {
  if (!securityControls) {
    return 'warning';
  }
  return securityControls.secure_headers_enabled && securityControls.secure_headers_hsts_enabled ? 'success' : 'danger';
}

function summarizeBackupTone(observabilitySummary: ControlPlaneObservabilitySummary | null): PlatformTone {
  if (!observabilitySummary) {
    return 'warning';
  }
  return observabilitySummary.backup.status === 'ok' ? 'success' : 'danger';
}

function summarizeOperationsTone(observabilitySummary: ControlPlaneObservabilitySummary | null): PlatformTone {
  if (!observabilitySummary) {
    return 'warning';
  }
  return observabilitySummary.operations.dead_letter_count > 0 || observabilitySummary.runtime.degraded_branch_count > 0
    ? 'danger'
    : 'success';
}

export function buildPlatformAdminOverviewModel(input: {
  observabilitySummary: ControlPlaneObservabilitySummary | null;
  securityControls: ControlPlaneSystemSecurityControls | null;
  environmentContract: ControlPlaneSystemEnvironmentContract | null;
  tenants: ControlPlanePlatformTenantRecord[];
  activeTenantLifecycle: ControlPlaneTenantLifecycleSummary | null;
}): PlatformAdminOverviewModel {
  const {
    observabilitySummary,
    securityControls,
    environmentContract,
    tenants,
    activeTenantLifecycle,
  } = input;

  const healthTone = resolveReleaseHealthTone(observabilitySummary, securityControls, environmentContract);
  const healthLabel = healthTone === 'success' ? 'Healthy' : healthTone === 'danger' ? 'Attention required' : 'Pending';

  const criticalExceptions: PlatformException[] = [];
  if (observabilitySummary?.operations.dead_letter_count) {
    criticalExceptions.push({
      id: 'dead-letter-jobs',
      title: 'Dead-letter operations jobs',
      detail: `${observabilitySummary.operations.dead_letter_count} jobs require intervention in the operations queue.`,
      tone: 'danger',
    });
  }
  if (observabilitySummary?.runtime.degraded_branch_count) {
    criticalExceptions.push({
      id: 'degraded-branches',
      title: 'Degraded branch runtime posture',
      detail: `${observabilitySummary.runtime.degraded_branch_count} branches are degraded across the current environment.`,
      tone: 'danger',
    });
  }
  if (observabilitySummary && observabilitySummary.backup.status !== 'ok') {
    criticalExceptions.push({
      id: 'backup-status',
      title: 'Backup posture requires attention',
      detail: `Backup status is ${observabilitySummary.backup.status}. Review freshness and restore readiness before the next release.`,
      tone: 'danger',
    });
  }
  if (securityControls && (!securityControls.secure_headers_enabled || !securityControls.secure_headers_hsts_enabled)) {
    criticalExceptions.push({
      id: 'security-headers',
      title: 'Secure header posture is incomplete',
      detail: 'Secure headers or HSTS are not fully enabled for the deployed control plane.',
      tone: 'warning',
    });
  }
  if (environmentContract && !environmentContract.object_storage_configured) {
    criticalExceptions.push({
      id: 'object-storage',
      title: 'Object storage is not configured',
      detail: 'Evidence retention and backup workflows will not be fully durable without object storage.',
      tone: 'warning',
    });
  }

  const tenantExceptions = tenants
    .filter((tenant) => tenant.status !== 'ACTIVE' || tenant.onboarding_status !== 'BRANCH_READY')
    .map<PlatformException>((tenant) => ({
      id: tenant.tenant_id,
      title: tenant.name,
      detail: `${tenant.status} tenant with onboarding state ${tenant.onboarding_status}.`,
      tone: tenant.status === 'ACTIVE' ? 'warning' : 'danger',
    }));

  if (activeTenantLifecycle && activeTenantLifecycle.entitlement.lifecycle_status !== 'ACTIVE' && activeTenantLifecycle.entitlement.lifecycle_status !== 'TRIALING') {
    tenantExceptions.unshift({
      id: `${activeTenantLifecycle.tenant_id}-lifecycle`,
      title: 'Selected tenant entitlement requires review',
      detail: `Tenant ${activeTenantLifecycle.tenant_id} is ${activeTenantLifecycle.entitlement.lifecycle_status}.`,
      tone: 'warning',
    });
  }

  return {
    commandContext: {
      environmentLabel: environmentContract?.deployment_environment ?? observabilitySummary?.environment ?? 'Unknown environment',
      releaseLabel: environmentContract?.release_version ?? observabilitySummary?.release_version ?? 'Unknown release',
      healthLabel,
      healthTone,
    },
    postureSignals: [
      {
        label: 'Release readiness',
        value: healthLabel,
        tone: healthTone,
      },
      {
        label: 'Security posture',
        value: securityControls
          ? (securityControls.secure_headers_enabled && securityControls.secure_headers_hsts_enabled ? 'Headers enforced' : 'Header gaps')
          : 'Unavailable',
        tone: summarizeSecurityTone(securityControls),
      },
      {
        label: 'Operations',
        value: observabilitySummary
          ? `${observabilitySummary.operations.dead_letter_count} dead-letter / ${observabilitySummary.runtime.degraded_branch_count} degraded`
          : 'Unavailable',
        tone: summarizeOperationsTone(observabilitySummary),
      },
      {
        label: 'Backup / restore',
        value: observabilitySummary?.backup.status?.toUpperCase() ?? 'Unavailable',
        tone: summarizeBackupTone(observabilitySummary),
      },
    ],
    criticalExceptions,
    tenantExceptions,
    runtimeHighlights: [
      {
        label: 'Queue posture',
        value: observabilitySummary
          ? `${observabilitySummary.operations.queued_count} queued / ${observabilitySummary.operations.running_count} running`
          : 'Unavailable',
      },
      {
        label: 'Retryable failures',
        value: observabilitySummary ? String(observabilitySummary.operations.retryable_count) : 'Unavailable',
        tone: observabilitySummary && observabilitySummary.operations.retryable_count > 0 ? 'warning' : 'success',
      },
      {
        label: 'Tracked branches',
        value: observabilitySummary ? String(observabilitySummary.runtime.tracked_branch_count) : 'Unavailable',
      },
      {
        label: 'Max outbox depth',
        value: observabilitySummary ? String(observabilitySummary.runtime.max_local_outbox_depth) : 'Unavailable',
      },
    ],
    releaseHighlights: [
      {
        label: 'Public base URL',
        value: environmentContract?.public_base_url ?? observabilitySummary?.system_health.public_base_url ?? 'Unavailable',
      },
      {
        label: 'Object storage',
        value: environmentContract?.object_storage_configured
          ? environmentContract.object_storage_bucket ?? 'Configured'
          : 'Not configured',
        tone: environmentContract?.object_storage_configured ? 'success' : 'warning',
      },
      {
        label: 'Rate limit window',
        value: securityControls ? `${securityControls.rate_limits.window_seconds}s` : 'Unavailable',
      },
      {
        label: 'Backup release',
        value: observabilitySummary?.backup.release_version ?? 'Unavailable',
      },
    ],
  };
}
