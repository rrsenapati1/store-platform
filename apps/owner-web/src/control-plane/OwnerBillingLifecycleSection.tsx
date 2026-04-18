import { startTransition, useState } from 'react';
import { ActionButton, DetailList, SectionCard, StatusBadge } from '@store/ui';
import type { ControlPlaneSubscriptionBootstrap, ControlPlaneTenantLifecycleSummary } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerBillingLifecycleSectionProps = {
  accessToken: string;
  tenantId: string;
};

function statusTone(status: string): 'neutral' | 'success' | 'warning' {
  if (status === 'ACTIVE') {
    return 'success';
  }
  if (status === 'GRACE' || status === 'TRIALING' || status === 'SUSPENDED') {
    return 'warning';
  }
  return 'neutral';
}

function formatPlanLabel(planCode: string): string {
  return planCode
    .split('-')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
}

function providerLabel(summary: ControlPlaneTenantLifecycleSummary | null): string {
  return summary?.subscription?.provider_name ?? 'Not configured';
}

export function OwnerBillingLifecycleSection({ accessToken, tenantId }: OwnerBillingLifecycleSectionProps) {
  const [summary, setSummary] = useState<ControlPlaneTenantLifecycleSummary | null>(null);
  const [providerName, setProviderName] = useState('cashfree');
  const [latestCheckout, setLatestCheckout] = useState<ControlPlaneSubscriptionBootstrap | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadBillingLifecycle() {
    if (!accessToken || !tenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const lifecycle = await ownerControlPlaneClient.getTenantBillingLifecycle(accessToken, tenantId);
      startTransition(() => {
        setSummary(lifecycle);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load billing lifecycle');
    } finally {
      setIsBusy(false);
    }
  }

  async function startRecurringSubscription() {
    if (!accessToken || !tenantId || !providerName) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const checkout = await ownerControlPlaneClient.bootstrapTenantSubscription(accessToken, tenantId, {
        provider_name: providerName,
      });
      startTransition(() => {
        setLatestCheckout(checkout);
        setSummary((current) =>
          current
            ? {
                ...current,
                subscription: {
                  ...current.subscription,
                  provider_name: checkout.provider_name,
                  provider_customer_id: checkout.provider_customer_id,
                  provider_subscription_id: checkout.provider_subscription_id,
                  mandate_status: checkout.mandate_status,
                },
              }
            : current,
        );
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to start recurring subscription');
    } finally {
      setIsBusy(false);
    }
  }

  const isSuspended = summary?.entitlement?.lifecycle_status === 'SUSPENDED';
  const isGrace = summary?.entitlement?.lifecycle_status === 'GRACE';
  const activePlanCode = summary?.entitlement?.active_plan_code;
  const subscriptionStatus = summary?.subscription?.lifecycle_status;
  const entitlementStatus = summary?.entitlement?.lifecycle_status;
  const mandateStatus = summary?.subscription?.mandate_status;
  const trialEndsAt = summary?.subscription?.trial_ends_at;
  const graceUntil = summary?.entitlement?.grace_until;
  const branchLimit = summary?.entitlement?.branch_limit;
  const deviceLimit = summary?.entitlement?.device_limit;
  const offlineRuntimeHours = summary?.entitlement?.offline_runtime_hours;

  return (
    <SectionCard eyebrow="Tenant billing lifecycle" title="Subscription and entitlement">
      <ActionButton onClick={() => void loadBillingLifecycle()} disabled={isBusy || !accessToken || !tenantId}>
        Load billing status
      </ActionButton>

      <div style={{ display: 'grid', gap: '8px', marginTop: '16px' }}>
        <label
          htmlFor="tenant-recurring-provider"
          style={{ display: 'grid', gap: '8px', marginBottom: '14px', color: '#25314f' }}
        >
          <span style={{ fontSize: '13px', fontWeight: 600 }}>Recurring provider</span>
          <select
            id="tenant-recurring-provider"
            value={providerName}
            onChange={(event) => setProviderName(event.target.value)}
            style={{
              border: '1px solid rgb(215, 219, 234)',
              borderRadius: '12px',
              color: '#1d2433',
              fontSize: '0.95rem',
              minHeight: '48px',
              padding: '0 14px',
            }}
          >
            <option value="cashfree">cashfree</option>
            <option value="razorpay">razorpay</option>
          </select>
        </label>
        <ActionButton onClick={() => void startRecurringSubscription()} disabled={isBusy || !accessToken || !tenantId || !providerName}>
          Start recurring subscription
        </ActionButton>
      </div>

      {summary ? (
        <div style={{ marginTop: '16px' }}>
          <DetailList
            items={[
              { label: 'Plan', value: activePlanCode ? formatPlanLabel(activePlanCode) : 'Unavailable' },
              {
                label: 'Subscription status',
                value: <StatusBadge label={subscriptionStatus ?? 'UNKNOWN'} tone={statusTone(subscriptionStatus ?? 'UNKNOWN')} />,
              },
              {
                label: 'Entitlement status',
                value: <StatusBadge label={entitlementStatus ?? 'UNKNOWN'} tone={statusTone(entitlementStatus ?? 'UNKNOWN')} />,
              },
              { label: 'Provider', value: providerLabel(summary) },
              { label: 'Mandate status', value: mandateStatus ?? 'Pending setup' },
              { label: 'Trial ends', value: trialEndsAt ?? 'Unavailable' },
              { label: 'Grace until', value: graceUntil ?? 'Unavailable' },
              { label: 'Branch limit', value: branchLimit == null ? 'Unavailable' : String(branchLimit) },
              { label: 'Device limit', value: deviceLimit == null ? 'Unavailable' : String(deviceLimit) },
              { label: 'Offline hours', value: offlineRuntimeHours == null ? 'Unavailable' : String(offlineRuntimeHours) },
            ]}
          />
        </div>
      ) : null}

      {isSuspended ? (
        <p style={{ color: '#9d2b19', marginBottom: 0, marginTop: '16px' }}>
          Commercial access suspended. Renew the subscription mandate or complete a recovery payment to restore owner and runtime access.
        </p>
      ) : null}

      {isGrace ? (
        <p style={{ color: '#7a5c1b', marginBottom: 0, marginTop: '16px' }}>
          Renewal grace window is active. Complete the recurring mandate setup before entitlement suspension.
        </p>
      ) : null}

      {latestCheckout ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest checkout session</h3>
          <DetailList
            items={[
              { label: 'Provider', value: latestCheckout.provider_name },
              { label: 'Mandate status', value: latestCheckout.mandate_status },
              { label: 'Customer reference', value: latestCheckout.provider_customer_id },
              { label: 'Subscription reference', value: latestCheckout.provider_subscription_id },
              {
                label: 'Checkout URL',
                value: (
                  <a href={latestCheckout.checkout_url} target="_blank" rel="noreferrer">
                    {latestCheckout.checkout_url}
                  </a>
                ),
              },
            ]}
          />
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
