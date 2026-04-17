import { startTransition, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard } from '@store/ui';
import type { ControlPlaneGiftCard, ControlPlaneGiftCardRecord } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerGiftCardSectionProps = {
  accessToken: string;
  tenantId: string;
};

function summarizeGiftCard(record: ControlPlaneGiftCardRecord): string {
  return `${record.display_name} (${record.gift_card_code}) ${record.status}`;
}

export function OwnerGiftCardSection({ accessToken, tenantId }: OwnerGiftCardSectionProps) {
  const [giftCards, setGiftCards] = useState<ControlPlaneGiftCardRecord[]>([]);
  const [selectedGiftCard, setSelectedGiftCard] = useState<ControlPlaneGiftCard | null>(null);
  const [selectedGiftCardId, setSelectedGiftCardId] = useState('');
  const [query, setQuery] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [giftCardCode, setGiftCardCode] = useState('');
  const [initialAmount, setInitialAmount] = useState('');
  const [issueNote, setIssueNote] = useState('');
  const [adjustDelta, setAdjustDelta] = useState('');
  const [adjustNote, setAdjustNote] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  function clearIssueDraft() {
    setDisplayName('');
    setGiftCardCode('');
    setInitialAmount('');
    setIssueNote('');
  }

  function clearAdjustDraft() {
    setAdjustDelta('');
    setAdjustNote('');
  }

  async function selectGiftCard(giftCardId: string) {
    if (!accessToken || !tenantId || !giftCardId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const giftCard = await ownerControlPlaneClient.getGiftCard(accessToken, tenantId, giftCardId);
      startTransition(() => {
        setSelectedGiftCard(giftCard);
        setSelectedGiftCardId(giftCard.id);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load gift card.');
    } finally {
      setIsBusy(false);
    }
  }

  async function loadGiftCards() {
    if (!accessToken || !tenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.listGiftCards(accessToken, tenantId, query || undefined);
      const nextSelectedId = selectedGiftCardId || (response.records[0]?.id ?? '');
      const selected = nextSelectedId
        ? await ownerControlPlaneClient.getGiftCard(accessToken, tenantId, nextSelectedId)
        : null;
      startTransition(() => {
        setGiftCards(response.records);
        setSelectedGiftCard(selected);
        setSelectedGiftCardId(selected?.id ?? '');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load gift cards.');
    } finally {
      setIsBusy(false);
    }
  }

  async function issueGiftCard() {
    if (!accessToken || !tenantId) {
      return;
    }
    const parsedInitialAmount = Number(initialAmount);
    if (!Number.isFinite(parsedInitialAmount) || parsedInitialAmount <= 0) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const created = await ownerControlPlaneClient.createGiftCard(accessToken, tenantId, {
        display_name: displayName,
        gift_card_code: giftCardCode.toUpperCase(),
        initial_amount: parsedInitialAmount,
        note: issueNote || null,
      });
      startTransition(() => {
        setGiftCards((current) => [created, ...current.filter((record) => record.id !== created.id)]);
        setSelectedGiftCard(created);
        setSelectedGiftCardId(created.id);
        clearIssueDraft();
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to issue gift card.');
    } finally {
      setIsBusy(false);
    }
  }

  async function adjustSelectedGiftCard() {
    if (!accessToken || !tenantId || !selectedGiftCard) {
      return;
    }
    const amountDelta = Number(adjustDelta);
    if (!Number.isFinite(amountDelta) || amountDelta === 0) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = await ownerControlPlaneClient.adjustGiftCard(accessToken, tenantId, selectedGiftCard.id, {
        amount_delta: amountDelta,
        note: adjustNote || null,
      });
      startTransition(() => {
        setGiftCards((current) => current.map((record) => (record.id === updated.id ? updated : record)));
        setSelectedGiftCard(updated);
        clearAdjustDraft();
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to adjust gift card.');
    } finally {
      setIsBusy(false);
    }
  }

  async function disableSelectedGiftCard() {
    if (!accessToken || !tenantId || !selectedGiftCard) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = await ownerControlPlaneClient.disableGiftCard(accessToken, tenantId, selectedGiftCard.id);
      startTransition(() => {
        setGiftCards((current) => current.map((record) => (record.id === updated.id ? updated : record)));
        setSelectedGiftCard(updated);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to disable gift card.');
    } finally {
      setIsBusy(false);
    }
  }

  async function reactivateSelectedGiftCard() {
    if (!accessToken || !tenantId || !selectedGiftCard) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = await ownerControlPlaneClient.reactivateGiftCard(accessToken, tenantId, selectedGiftCard.id);
      startTransition(() => {
        setGiftCards((current) => current.map((record) => (record.id === updated.id ? updated : record)));
        setSelectedGiftCard(updated);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to reactivate gift card.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Tenant liability instruments" title="Gift cards">
      <FormField id="gift-card-search" label="Gift card search" value={query} onChange={setQuery} />
      <ActionButton onClick={() => void loadGiftCards()} disabled={isBusy || !accessToken || !tenantId}>
        Load gift cards
      </ActionButton>

      <div style={{ marginTop: '20px' }}>
        <h3 style={{ marginBottom: '10px' }}>Issue gift card</h3>
        <FormField id="gift-card-display-name" label="Gift card display name" value={displayName} onChange={setDisplayName} />
        <FormField id="gift-card-code" label="Gift card code" value={giftCardCode} onChange={(value) => setGiftCardCode(value.toUpperCase())} />
        <FormField id="gift-card-initial-amount" label="Initial amount" value={initialAmount} onChange={setInitialAmount} />
        <FormField id="gift-card-issue-note" label="Issue note" value={issueNote} onChange={setIssueNote} />
        <ActionButton
          onClick={() => void issueGiftCard()}
          disabled={isBusy || !displayName.trim() || !giftCardCode.trim() || !initialAmount.trim()}
        >
          Issue gift card
        </ActionButton>
      </div>

      {giftCards.length ? (
        <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {giftCards.map((giftCard) => (
            <li key={giftCard.id}>
              <button
                type="button"
                onClick={() => void selectGiftCard(giftCard.id)}
                style={{ background: 'none', border: 0, color: '#25314f', cursor: 'pointer', fontWeight: 600, padding: 0 }}
              >
                {summarizeGiftCard(giftCard)}
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {selectedGiftCard ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Gift card details</h3>
          <p style={{ color: '#75809b', fontSize: '12px', letterSpacing: '0.12em', marginBottom: '12px', textTransform: 'uppercase' }}>
            {selectedGiftCard.status}
          </p>
          <DetailList
            items={[
              { label: 'Gift card code', value: selectedGiftCard.gift_card_code },
              { label: 'Display name', value: selectedGiftCard.display_name },
              { label: 'Available balance', value: String(selectedGiftCard.available_balance) },
              { label: 'Issued total', value: String(selectedGiftCard.issued_total) },
              { label: 'Redeemed total', value: String(selectedGiftCard.redeemed_total) },
              { label: 'Adjusted total', value: String(selectedGiftCard.adjusted_total) },
            ]}
          />
          <div style={{ display: 'grid', gap: '12px', marginTop: '16px' }}>
            <FormField id="gift-card-adjust-delta" label="Adjust balance delta" value={adjustDelta} onChange={setAdjustDelta} />
            <FormField id="gift-card-adjust-note" label="Adjust note" value={adjustNote} onChange={setAdjustNote} />
            <ActionButton onClick={() => void adjustSelectedGiftCard()} disabled={isBusy}>
              Adjust selected gift card
            </ActionButton>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginTop: '16px' }}>
            {selectedGiftCard.status === 'ACTIVE' ? (
              <ActionButton onClick={() => void disableSelectedGiftCard()} disabled={isBusy}>
                Disable selected gift card
              </ActionButton>
            ) : (
              <ActionButton onClick={() => void reactivateSelectedGiftCard()} disabled={isBusy}>
                Reactivate selected gift card
              </ActionButton>
            )}
          </div>
          {selectedGiftCard.ledger_entries.length ? (
            <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
              {selectedGiftCard.ledger_entries.map((entry) => (
                <li key={entry.id}>
                  {entry.entry_type} {entry.source_type} {entry.amount} {entry.note ? `- ${entry.note}` : ''}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
