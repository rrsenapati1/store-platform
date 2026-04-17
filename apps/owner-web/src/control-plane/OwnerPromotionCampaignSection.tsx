import { useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { ControlPlanePromotionCampaign } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerPromotionCampaignSectionProps = {
  accessToken: string;
  tenantId: string;
};

type PromotionCampaignDraft = {
  name: string;
  status: string;
  triggerMode: string;
  scope: string;
  discountType: string;
  discountValue: string;
  priority: string;
  stackingRule: string;
  minimumOrderAmount: string;
  maximumDiscountAmount: string;
  redemptionLimitTotal: string;
  targetProductIds: string;
  targetCategoryCodes: string;
};

function defaultCampaignDraft(): PromotionCampaignDraft {
  return {
    name: '',
    status: 'ACTIVE',
    triggerMode: 'CODE',
    scope: 'CART',
    discountType: 'FLAT_AMOUNT',
    discountValue: '0',
    priority: '100',
    stackingRule: 'STACKABLE',
    minimumOrderAmount: '',
    maximumDiscountAmount: '',
    redemptionLimitTotal: '',
    targetProductIds: '',
    targetCategoryCodes: '',
  };
}

function buildCampaignDraft(campaign: ControlPlanePromotionCampaign): PromotionCampaignDraft {
  return {
    name: campaign.name,
    status: campaign.status,
    triggerMode: campaign.trigger_mode ?? 'CODE',
    scope: campaign.scope ?? 'CART',
    discountType: campaign.discount_type,
    discountValue: String(campaign.discount_value),
    priority: String(campaign.priority ?? 100),
    stackingRule: campaign.stacking_rule ?? 'STACKABLE',
    minimumOrderAmount: campaign.minimum_order_amount == null ? '' : String(campaign.minimum_order_amount),
    maximumDiscountAmount: campaign.maximum_discount_amount == null ? '' : String(campaign.maximum_discount_amount),
    redemptionLimitTotal: campaign.redemption_limit_total == null ? '' : String(campaign.redemption_limit_total),
    targetProductIds: Array.isArray(campaign.target_product_ids) ? campaign.target_product_ids.join(', ') : '',
    targetCategoryCodes: Array.isArray(campaign.target_category_codes) ? campaign.target_category_codes.join(', ') : '',
  };
}

function parseOptionalNumber(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  return Number(trimmed);
}

function parseCsvValues(value: string): string[] | null {
  const records = value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean);
  return records.length ? records : null;
}

export function OwnerPromotionCampaignSection({
  accessToken,
  tenantId,
}: OwnerPromotionCampaignSectionProps) {
  const [campaigns, setCampaigns] = useState<ControlPlanePromotionCampaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState('');
  const [campaignDraft, setCampaignDraft] = useState<PromotionCampaignDraft>(defaultCampaignDraft());
  const [sharedCodeDraft, setSharedCodeDraft] = useState('');
  const [sharedCodeStatus, setSharedCodeStatus] = useState('ACTIVE');
  const [sharedCodeLimit, setSharedCodeLimit] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  const selectedCampaign = campaigns.find((campaign) => campaign.id === selectedCampaignId) ?? null;
  const isAutomaticDraft = campaignDraft.triggerMode === 'AUTOMATIC';
  const isAssignedVoucherDraft = campaignDraft.triggerMode === 'ASSIGNED_VOUCHER';
  const isAutomaticItemCategoryDraft = isAutomaticDraft && campaignDraft.scope === 'ITEM_CATEGORY';
  const selectedCampaignSupportsSharedCodes = selectedCampaign?.trigger_mode === 'CODE';

  function applySelectedCampaign(campaign: ControlPlanePromotionCampaign | null) {
    setSelectedCampaignId(campaign?.id ?? '');
    setCampaignDraft(campaign ? buildCampaignDraft(campaign) : defaultCampaignDraft());
    setSharedCodeDraft('');
    setSharedCodeStatus('ACTIVE');
    setSharedCodeLimit('');
  }

  async function loadCampaigns(preferredCampaignId?: string) {
    if (!accessToken || !tenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.listPromotionCampaigns(accessToken, tenantId);
      const records = Array.isArray(response.records)
        ? response.records.map((campaign) => ({
          ...campaign,
          codes: Array.isArray(campaign.codes) ? campaign.codes : [],
        }))
        : [];
      setCampaigns(records);
      const nextCampaign =
        records.find((campaign) => campaign.id === (preferredCampaignId ?? selectedCampaignId))
        ?? records[0]
        ?? null;
      applySelectedCampaign(nextCampaign);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load promotion campaigns');
    } finally {
      setIsBusy(false);
    }
  }

  async function createCampaign() {
    if (!accessToken || !tenantId || !campaignDraft.name.trim()) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const created = await ownerControlPlaneClient.createPromotionCampaign(accessToken, tenantId, {
        name: campaignDraft.name.trim(),
        status: campaignDraft.status,
        trigger_mode: campaignDraft.triggerMode,
        scope: campaignDraft.scope,
        discount_type: campaignDraft.discountType,
        discount_value: Number(campaignDraft.discountValue || 0),
        priority: Number(campaignDraft.priority || 100),
        stacking_rule: campaignDraft.stackingRule,
        minimum_order_amount: parseOptionalNumber(campaignDraft.minimumOrderAmount),
        maximum_discount_amount: parseOptionalNumber(campaignDraft.maximumDiscountAmount),
        redemption_limit_total: parseOptionalNumber(campaignDraft.redemptionLimitTotal),
        target_product_ids: parseCsvValues(campaignDraft.targetProductIds),
        target_category_codes: parseCsvValues(campaignDraft.targetCategoryCodes),
      });
      await loadCampaigns(created.id);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create promotion campaign');
    } finally {
      setIsBusy(false);
    }
  }

  async function saveSelectedCampaign() {
    if (!accessToken || !tenantId || !selectedCampaign) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = await ownerControlPlaneClient.updatePromotionCampaign(accessToken, tenantId, selectedCampaign.id, {
        name: campaignDraft.name.trim(),
        status: campaignDraft.status,
        trigger_mode: campaignDraft.triggerMode,
        scope: campaignDraft.scope,
        discount_type: campaignDraft.discountType,
        discount_value: Number(campaignDraft.discountValue || 0),
        priority: Number(campaignDraft.priority || 100),
        stacking_rule: campaignDraft.stackingRule,
        minimum_order_amount: parseOptionalNumber(campaignDraft.minimumOrderAmount),
        maximum_discount_amount: parseOptionalNumber(campaignDraft.maximumDiscountAmount),
        redemption_limit_total: parseOptionalNumber(campaignDraft.redemptionLimitTotal),
        target_product_ids: parseCsvValues(campaignDraft.targetProductIds),
        target_category_codes: parseCsvValues(campaignDraft.targetCategoryCodes),
      });
      await loadCampaigns(updated.id);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to save promotion campaign');
    } finally {
      setIsBusy(false);
    }
  }

  async function toggleSelectedCampaignStatus() {
    if (!accessToken || !tenantId || !selectedCampaign) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = selectedCampaign.status === 'ACTIVE'
        ? await ownerControlPlaneClient.disablePromotionCampaign(accessToken, tenantId, selectedCampaign.id)
        : await ownerControlPlaneClient.reactivatePromotionCampaign(accessToken, tenantId, selectedCampaign.id);
      await loadCampaigns(updated.id);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to update promotion campaign status');
    } finally {
      setIsBusy(false);
    }
  }

  async function createSharedCode() {
    if (!accessToken || !tenantId || !selectedCampaign || selectedCampaign.trigger_mode !== 'CODE' || !sharedCodeDraft.trim()) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      await ownerControlPlaneClient.createPromotionCode(accessToken, tenantId, selectedCampaign.id, {
        code: sharedCodeDraft.trim(),
        status: sharedCodeStatus,
        redemption_limit_per_code: parseOptionalNumber(sharedCodeLimit),
      });
      await loadCampaigns(selectedCampaign.id);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create shared promotion code');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Promotions foundation" title="Promotion campaigns">
      <div style={{ display: 'grid', gap: '12px' }}>
        <FormField id="promotion-campaign-name" label="Campaign name" value={campaignDraft.name} onChange={(value) => setCampaignDraft((current) => ({ ...current, name: value }))} />
        <FormField id="promotion-campaign-status" label="Campaign status" value={campaignDraft.status} onChange={(value) => setCampaignDraft((current) => ({ ...current, status: value }))} />
        <FormField id="promotion-campaign-trigger-mode" label="Trigger mode" value={campaignDraft.triggerMode} onChange={(value) => setCampaignDraft((current) => ({ ...current, triggerMode: value }))} />
        <FormField id="promotion-campaign-scope" label="Scope" value={campaignDraft.scope} onChange={(value) => setCampaignDraft((current) => ({ ...current, scope: value }))} />
        <FormField id="promotion-campaign-discount-type" label="Discount type" value={campaignDraft.discountType} onChange={(value) => setCampaignDraft((current) => ({ ...current, discountType: value }))} />
        <FormField id="promotion-campaign-discount-value" label="Discount value" value={campaignDraft.discountValue} onChange={(value) => setCampaignDraft((current) => ({ ...current, discountValue: value }))} />
        <FormField id="promotion-campaign-priority" label="Priority" value={campaignDraft.priority} onChange={(value) => setCampaignDraft((current) => ({ ...current, priority: value }))} />
        <FormField id="promotion-campaign-stacking-rule" label="Stacking rule" value={campaignDraft.stackingRule} onChange={(value) => setCampaignDraft((current) => ({ ...current, stackingRule: value }))} />
        <FormField id="promotion-campaign-minimum-order" label="Minimum order amount" value={campaignDraft.minimumOrderAmount} onChange={(value) => setCampaignDraft((current) => ({ ...current, minimumOrderAmount: value }))} />
        <FormField id="promotion-campaign-maximum-discount" label="Maximum discount amount" value={campaignDraft.maximumDiscountAmount} onChange={(value) => setCampaignDraft((current) => ({ ...current, maximumDiscountAmount: value }))} />
        <FormField id="promotion-campaign-redemption-limit" label="Total redemption limit" value={campaignDraft.redemptionLimitTotal} onChange={(value) => setCampaignDraft((current) => ({ ...current, redemptionLimitTotal: value }))} />
        {isAutomaticItemCategoryDraft ? (
          <>
            <FormField id="promotion-campaign-target-product-ids" label="Target product ids" value={campaignDraft.targetProductIds} onChange={(value) => setCampaignDraft((current) => ({ ...current, targetProductIds: value }))} />
            <FormField id="promotion-campaign-target-category-codes" label="Target category codes" value={campaignDraft.targetCategoryCodes} onChange={(value) => setCampaignDraft((current) => ({ ...current, targetCategoryCodes: value }))} />
          </>
        ) : null}
      </div>
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '14px' }}>
        <ActionButton onClick={() => void loadCampaigns()} disabled={isBusy}>
          Refresh promotion campaigns
        </ActionButton>
        <ActionButton onClick={() => void createCampaign()} disabled={isBusy || !campaignDraft.name.trim()}>
          Create promotion campaign
        </ActionButton>
        <ActionButton onClick={() => void saveSelectedCampaign()} disabled={isBusy || !selectedCampaign}>
          Save selected campaign
        </ActionButton>
        {selectedCampaign ? (
          <ActionButton onClick={() => void toggleSelectedCampaignStatus()} disabled={isBusy}>
            {selectedCampaign.status === 'ACTIVE' ? 'Disable selected campaign' : 'Reactivate selected campaign'}
          </ActionButton>
        ) : null}
      </div>

      {campaigns.length ? (
        <ul style={{ marginTop: '16px', marginBottom: '16px', color: '#4e5871', lineHeight: 1.7, paddingLeft: '20px' }}>
          {campaigns.map((campaign) => (
            <li key={campaign.id}>
              <ActionButton onClick={() => applySelectedCampaign(campaign)} disabled={isBusy}>
                {`Select campaign ${campaign.name}`}
              </ActionButton>
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ color: '#4e5871' }}>No promotion campaigns loaded yet.</p>
      )}

      {selectedCampaign ? (
        <>
          <DetailList
            items={[
              { label: 'Selected campaign', value: selectedCampaign.name },
              { label: 'Status', value: <StatusBadge label={selectedCampaign.status} tone={selectedCampaign.status === 'ACTIVE' ? 'success' : 'warning'} /> },
              { label: 'Trigger', value: selectedCampaign.trigger_mode ?? 'CODE' },
              { label: 'Scope', value: selectedCampaign.scope ?? 'CART' },
              { label: 'Discount rule', value: `${selectedCampaign.discount_type} ${selectedCampaign.discount_value}` },
              { label: 'Priority', value: String(selectedCampaign.priority ?? 100) },
              { label: 'Stacking rule', value: selectedCampaign.stacking_rule ?? 'STACKABLE' },
              { label: 'Minimum order', value: selectedCampaign.minimum_order_amount == null ? 'None' : String(selectedCampaign.minimum_order_amount) },
              { label: 'Maximum discount', value: selectedCampaign.maximum_discount_amount == null ? 'None' : String(selectedCampaign.maximum_discount_amount) },
              {
                label: 'Target products',
                value: Array.isArray(selectedCampaign.target_product_ids) && selectedCampaign.target_product_ids.length
                  ? selectedCampaign.target_product_ids.join(', ')
                  : 'None',
              },
              {
                label: 'Target categories',
                value: Array.isArray(selectedCampaign.target_category_codes) && selectedCampaign.target_category_codes.length
                  ? selectedCampaign.target_category_codes.join(', ')
                  : 'None',
              },
              { label: 'Total redemption count', value: String(selectedCampaign.redemption_count) },
            ]}
          />

          {selectedCampaignSupportsSharedCodes ? (
            <>
              <div style={{ marginTop: '16px', display: 'grid', gap: '12px' }}>
                <FormField id="promotion-shared-code" label="Shared promotion code" value={sharedCodeDraft} onChange={setSharedCodeDraft} />
                <FormField id="promotion-shared-code-status" label="Shared code status" value={sharedCodeStatus} onChange={setSharedCodeStatus} />
                <FormField id="promotion-shared-code-limit" label="Per-code redemption limit" value={sharedCodeLimit} onChange={setSharedCodeLimit} />
              </div>
              <div style={{ marginTop: '14px' }}>
                <ActionButton onClick={() => void createSharedCode()} disabled={isBusy || !sharedCodeDraft.trim()}>
                  Create shared code
                </ActionButton>
              </div>

              {selectedCampaign.codes.length ? (
                <ul style={{ marginTop: '16px', marginBottom: 0, color: '#4e5871', lineHeight: 1.7, paddingLeft: '20px' }}>
                  {selectedCampaign.codes.map((code) => (
                    <li key={code.id}>
                      {code.code} - {code.status} - redeemed {code.redemption_count}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: '#4e5871' }}>No shared codes created for this campaign yet.</p>
              )}
            </>
          ) : (
            <p style={{ color: '#4e5871' }}>
              {selectedCampaign.trigger_mode === 'ASSIGNED_VOUCHER'
                ? 'Assigned voucher campaigns are issued to one customer profile at a time and do not use shared codes.'
                : 'Automatic campaigns apply without cashier-entered shared codes.'}
            </p>
          )}
        </>
      ) : null}

      {isAssignedVoucherDraft ? (
        <p style={{ color: '#4e5871' }}>
          Assigned voucher campaigns are fixed-value, customer-specific voucher templates. Issue the actual voucher from customer insights.
        </p>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
