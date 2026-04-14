import { startTransition, useState } from 'react';
import type { ControlPlaneActor, ControlPlaneInvite, ControlPlanePlatformTenantRecord } from '@store/types';
import { platformAdminClient } from './client';

export function usePlatformAdminWorkspace() {
  const [korsenexToken, setKorsenexToken] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [actor, setActor] = useState<ControlPlaneActor | null>(null);
  const [tenants, setTenants] = useState<ControlPlanePlatformTenantRecord[]>([]);
  const [activeTenantId, setActiveTenantId] = useState('');
  const [tenantName, setTenantName] = useState('');
  const [tenantSlug, setTenantSlug] = useState('');
  const [ownerEmail, setOwnerEmail] = useState('');
  const [ownerFullName, setOwnerFullName] = useState('');
  const [latestInvite, setLatestInvite] = useState<ControlPlaneInvite | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function startSession() {
    setIsBusy(true);
    setErrorMessage('');
    try {
      const session = await platformAdminClient.exchangeSession(korsenexToken);
      const [nextActor, tenantList] = await Promise.all([
        platformAdminClient.getActor(session.access_token),
        platformAdminClient.listTenants(session.access_token),
      ]);
      startTransition(() => {
        setAccessToken(session.access_token);
        setActor(nextActor);
        setTenants(tenantList.records);
        setActiveTenantId(tenantList.records[0]?.tenant_id ?? '');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to start session');
    } finally {
      setIsBusy(false);
    }
  }

  async function createTenant() {
    if (!accessToken) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const createdTenant = await platformAdminClient.createTenant(accessToken, {
        name: tenantName,
        slug: tenantSlug,
      });
      const tenantList = await platformAdminClient.listTenants(accessToken);
      startTransition(() => {
        setTenants(tenantList.records);
        setActiveTenantId(createdTenant.id);
        setTenantName('');
        setTenantSlug('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create tenant');
    } finally {
      setIsBusy(false);
    }
  }

  async function sendOwnerInvite() {
    if (!accessToken || !activeTenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const invite = await platformAdminClient.createOwnerInvite(accessToken, activeTenantId, {
        email: ownerEmail,
        full_name: ownerFullName,
      });
      startTransition(() => {
        setLatestInvite(invite);
        setOwnerEmail('');
        setOwnerFullName('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to send owner invite');
    } finally {
      setIsBusy(false);
    }
  }

  return {
    actor,
    activeTenantId,
    errorMessage,
    isBusy,
    korsenexToken,
    latestInvite,
    ownerEmail,
    ownerFullName,
    tenantName,
    tenantSlug,
    tenants,
    setActiveTenantId,
    setKorsenexToken,
    setOwnerEmail,
    setOwnerFullName,
    setTenantName,
    setTenantSlug,
    createTenant,
    sendOwnerInvite,
    startSession,
  };
}
