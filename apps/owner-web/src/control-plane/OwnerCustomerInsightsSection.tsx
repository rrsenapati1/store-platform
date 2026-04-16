import { startTransition, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard } from '@store/ui';
import type {
  ControlPlaneBranchCustomerReport,
  ControlPlaneCustomerDirectoryRecord,
  ControlPlaneCustomerHistoryResponse,
  ControlPlaneCustomerProfile,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerCustomerInsightsSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

type CustomerProfileDraft = {
  fullName: string;
  phone: string;
  email: string;
  gstin: string;
  defaultNote: string;
  tags: string;
};

function buildProfileDraft(profile: ControlPlaneCustomerProfile): CustomerProfileDraft {
  return {
    fullName: profile.full_name,
    phone: profile.phone ?? '',
    email: profile.email ?? '',
    gstin: profile.gstin ?? '',
    defaultNote: profile.default_note ?? '',
    tags: profile.tags.join(', '),
  };
}

function profileSummary(record: ControlPlaneCustomerProfile): string {
  const segments = [record.full_name];
  if (record.gstin) {
    segments.push(`(${record.gstin})`);
  }
  segments.push(record.status);
  return segments.join(' ');
}

export function OwnerCustomerInsightsSection({ accessToken, tenantId, branchId }: OwnerCustomerInsightsSectionProps) {
  const [directory, setDirectory] = useState<ControlPlaneCustomerDirectoryRecord[]>([]);
  const [branchReport, setBranchReport] = useState<ControlPlaneBranchCustomerReport | null>(null);
  const [customerProfiles, setCustomerProfiles] = useState<ControlPlaneCustomerProfile[]>([]);
  const [profileSearchQuery, setProfileSearchQuery] = useState('');
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [selectedProfile, setSelectedProfile] = useState<ControlPlaneCustomerProfile | null>(null);
  const [profileDraft, setProfileDraft] = useState<CustomerProfileDraft>({
    fullName: '',
    phone: '',
    email: '',
    gstin: '',
    defaultNote: '',
    tags: '',
  });
  const [customerHistory, setCustomerHistory] = useState<ControlPlaneCustomerHistoryResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  function applySelectedProfile(profile: ControlPlaneCustomerProfile | null) {
    setSelectedProfile(profile);
    setSelectedCustomerId(profile?.id ?? '');
    setProfileDraft(
      profile
        ? buildProfileDraft(profile)
        : {
            fullName: '',
            phone: '',
            email: '',
            gstin: '',
            defaultNote: '',
            tags: '',
          },
    );
  }

  async function loadCustomerInsights() {
    if (!accessToken || !tenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const [profilesResponse, directoryResponse, reportResponse] = await Promise.all([
        ownerControlPlaneClient.listCustomerProfiles(accessToken, tenantId, profileSearchQuery),
        ownerControlPlaneClient.listCustomers(accessToken, tenantId),
        branchId ? ownerControlPlaneClient.getBranchCustomerReport(accessToken, tenantId, branchId) : Promise.resolve(null),
      ]);
      const nextProfileId = profilesResponse.records[0]?.id ?? '';
      const [profile, history] = await Promise.all([
        nextProfileId ? ownerControlPlaneClient.getCustomerProfile(accessToken, tenantId, nextProfileId) : Promise.resolve(null),
        nextProfileId ? ownerControlPlaneClient.getCustomerHistory(accessToken, tenantId, nextProfileId) : Promise.resolve(null),
      ]);
      startTransition(() => {
        setCustomerProfiles(profilesResponse.records);
        setDirectory(directoryResponse.records);
        setBranchReport(reportResponse);
        applySelectedProfile(profile);
        setCustomerHistory(history);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load customer insights');
    } finally {
      setIsBusy(false);
    }
  }

  async function selectProfile(customerProfileId: string) {
    if (!accessToken || !tenantId || !customerProfileId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const [profile, history] = await Promise.all([
        ownerControlPlaneClient.getCustomerProfile(accessToken, tenantId, customerProfileId),
        ownerControlPlaneClient.getCustomerHistory(accessToken, tenantId, customerProfileId),
      ]);
      startTransition(() => {
        applySelectedProfile(profile);
        setCustomerHistory(history);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load customer profile');
    } finally {
      setIsBusy(false);
    }
  }

  async function saveSelectedCustomerProfile() {
    if (!accessToken || !tenantId || !selectedProfile) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = await ownerControlPlaneClient.updateCustomerProfile(accessToken, tenantId, selectedProfile.id, {
        full_name: profileDraft.fullName,
        phone: profileDraft.phone || null,
        email: profileDraft.email || null,
        gstin: profileDraft.gstin || null,
        default_note: profileDraft.defaultNote || null,
        tags: profileDraft.tags
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean),
      });
      startTransition(() => {
        setCustomerProfiles((current) => current.map((record) => (record.id === updated.id ? updated : record)));
        applySelectedProfile(updated);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to save customer profile');
    } finally {
      setIsBusy(false);
    }
  }

  async function archiveSelectedCustomerProfile() {
    if (!accessToken || !tenantId || !selectedProfile) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = await ownerControlPlaneClient.archiveCustomerProfile(accessToken, tenantId, selectedProfile.id);
      startTransition(() => {
        setCustomerProfiles((current) => current.map((record) => (record.id === updated.id ? updated : record)));
        applySelectedProfile(updated);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to archive customer profile');
    } finally {
      setIsBusy(false);
    }
  }

  async function reactivateSelectedCustomerProfile() {
    if (!accessToken || !tenantId || !selectedProfile) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = await ownerControlPlaneClient.reactivateCustomerProfile(accessToken, tenantId, selectedProfile.id);
      startTransition(() => {
        setCustomerProfiles((current) => current.map((record) => (record.id === updated.id ? updated : record)));
        applySelectedProfile(updated);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to reactivate customer profile');
    } finally {
      setIsBusy(false);
    }
  }

  async function loadSelectedCustomerHistory() {
    if (!accessToken || !tenantId || !selectedCustomerId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const history = await ownerControlPlaneClient.getCustomerHistory(accessToken, tenantId, selectedCustomerId);
      startTransition(() => {
        setCustomerHistory(history);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load customer history');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Customer reporting" title="Customer insights">
      <ActionButton onClick={() => void loadCustomerInsights()} disabled={isBusy || !accessToken || !tenantId}>
        Load customer insights
      </ActionButton>

      {branchReport ? (
        <div style={{ marginTop: '16px' }}>
          <DetailList
            items={[
              { label: 'Customers', value: String(branchReport.customer_count) },
              { label: 'Repeat customers', value: String(branchReport.repeat_customer_count) },
              { label: 'Anonymous sales', value: String(branchReport.anonymous_sales_count) },
              { label: 'Anonymous total', value: String(branchReport.anonymous_sales_total) },
            ]}
          />
        </div>
      ) : null}

      <div style={{ marginTop: '16px' }}>
        <FormField
          id="customer-profile-search"
          label="Customer profile search"
          value={profileSearchQuery}
          onChange={setProfileSearchQuery}
        />
      </div>

      {customerProfiles.length ? (
        <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {customerProfiles.map((record) => (
            <li key={record.id}>
              <button
                type="button"
                onClick={() => void selectProfile(record.id)}
                style={{ background: 'none', border: 0, color: '#25314f', cursor: 'pointer', fontWeight: 600, padding: 0 }}
              >
                {profileSummary(record)}
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {selectedProfile ? (
        <div style={{ marginTop: '16px' }}>
          <p style={{ color: '#75809b', fontSize: '12px', letterSpacing: '0.12em', marginBottom: '12px', textTransform: 'uppercase' }}>
            {selectedProfile.status}
          </p>
          <FormField
            id="profile-full-name"
            label="Profile full name"
            value={profileDraft.fullName}
            onChange={(value) => setProfileDraft((current) => ({ ...current, fullName: value }))}
          />
          <FormField
            id="profile-phone"
            label="Profile phone"
            value={profileDraft.phone}
            onChange={(value) => setProfileDraft((current) => ({ ...current, phone: value }))}
          />
          <FormField
            id="profile-email"
            label="Profile email"
            value={profileDraft.email}
            onChange={(value) => setProfileDraft((current) => ({ ...current, email: value }))}
          />
          <FormField
            id="profile-gstin"
            label="Profile GSTIN"
            value={profileDraft.gstin}
            onChange={(value) => setProfileDraft((current) => ({ ...current, gstin: value }))}
          />
          <FormField
            id="profile-note"
            label="Profile note"
            value={profileDraft.defaultNote}
            onChange={(value) => setProfileDraft((current) => ({ ...current, defaultNote: value }))}
          />
          <FormField
            id="profile-tags"
            label="Profile tags"
            value={profileDraft.tags}
            onChange={(value) => setProfileDraft((current) => ({ ...current, tags: value }))}
          />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginTop: '12px' }}>
            <ActionButton onClick={() => void saveSelectedCustomerProfile()} disabled={isBusy}>
              Save customer profile
            </ActionButton>
            {selectedProfile.status === 'ACTIVE' ? (
              <ActionButton onClick={() => void archiveSelectedCustomerProfile()} disabled={isBusy}>
                Archive customer profile
              </ActionButton>
            ) : (
              <ActionButton onClick={() => void reactivateSelectedCustomerProfile()} disabled={isBusy}>
                Reactivate customer profile
              </ActionButton>
            )}
          </div>
        </div>
      ) : null}

      {directory.length ? (
        <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {directory.map((record) => (
            <li key={record.customer_id}>
              {record.name} {record.gstin ? `(${record.gstin})` : ''} - visits {record.visit_count} - lifetime {record.lifetime_value}
            </li>
          ))}
        </ul>
      ) : null}

      <ActionButton onClick={() => void loadSelectedCustomerHistory()} disabled={isBusy || !selectedCustomerId}>
        Load selected customer history
      </ActionButton>

      {customerHistory ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Sales history</h3>
          <DetailList
            items={[
              { label: 'Sales', value: String(customerHistory.sales_summary.sales_count) },
              { label: 'Returns', value: String(customerHistory.sales_summary.return_count) },
              { label: 'Exchanges', value: String(customerHistory.sales_summary.exchange_count) },
              { label: 'Sales total', value: String(customerHistory.sales_summary.sales_total) },
            ]}
          />

          <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {customerHistory.sales.map((record) => (
              <li key={record.sale_id}>
                {record.invoice_number} - {record.payment_method} - {record.grand_total}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
