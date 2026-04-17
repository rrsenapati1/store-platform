import { startTransition } from 'react';
import type { ControlPlaneCashierSession } from '@store/types';
import { storeControlPlaneClient } from './client';

type SetString = (value: string) => void;

function resolveActiveCashierSession(
  sessions: ControlPlaneCashierSession[],
  selectedRuntimeDeviceId: string,
  actorUserId: string,
) {
  return sessions.find((session) => (
    session.status === 'OPEN'
    && session.device_registration_id === selectedRuntimeDeviceId
    && session.runtime_user_id === actorUserId
  )) ?? null;
}

function resolveCashierSessionRecords(
  response: { records?: ControlPlaneCashierSession[] | null },
): ControlPlaneCashierSession[] {
  return Array.isArray(response.records) ? response.records : [];
}

export async function runLoadCashierSessions(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  actorUserId: string;
  selectedRuntimeDeviceId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setCashierSessions: (value: ControlPlaneCashierSession[]) => void;
  setActiveCashierSession: (value: ControlPlaneCashierSession | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    actorUserId,
    selectedRuntimeDeviceId,
    setIsBusy,
    setErrorMessage,
    setCashierSessions,
    setActiveCashierSession,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const response = await storeControlPlaneClient.listCashierSessions(accessToken, tenantId, branchId, 'OPEN');
    const records = resolveCashierSessionRecords(response);
    startTransition(() => {
      setCashierSessions(records);
      setActiveCashierSession(resolveActiveCashierSession(records, selectedRuntimeDeviceId, actorUserId));
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load cashier sessions');
  } finally {
    setIsBusy(false);
  }
}

export async function runOpenCashierSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  deviceRegistrationId: string;
  staffProfileId: string;
  openingFloatAmount: number;
  openingNote: string;
  actorUserId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setCashierSessions: (value: ControlPlaneCashierSession[]) => void;
  setActiveCashierSession: (value: ControlPlaneCashierSession | null) => void;
  setCashierOpeningFloatAmount: (value: string) => void;
  setCashierOpeningNote: (value: string) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    deviceRegistrationId,
    staffProfileId,
    openingFloatAmount,
    openingNote,
    actorUserId,
    setIsBusy,
    setErrorMessage,
    setCashierSessions,
    setActiveCashierSession,
    setCashierOpeningFloatAmount,
    setCashierOpeningNote,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const session = await storeControlPlaneClient.createCashierSession(accessToken, tenantId, branchId, {
      device_registration_id: deviceRegistrationId,
      staff_profile_id: staffProfileId,
      opening_float_amount: openingFloatAmount,
      opening_note: openingNote || null,
    });
    const response = await storeControlPlaneClient.listCashierSessions(accessToken, tenantId, branchId, 'OPEN');
    const records = resolveCashierSessionRecords(response);
    startTransition(() => {
      setCashierSessions(records);
      setActiveCashierSession(resolveActiveCashierSession(records, deviceRegistrationId, actorUserId) ?? session);
      setCashierOpeningFloatAmount('');
      setCashierOpeningNote('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to open cashier session');
  } finally {
    setIsBusy(false);
  }
}

export async function runCloseCashierSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  cashierSessionId: string;
  actorUserId: string;
  selectedRuntimeDeviceId: string;
  closingNote: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setCashierSessions: (value: ControlPlaneCashierSession[]) => void;
  setActiveCashierSession: (value: ControlPlaneCashierSession | null) => void;
  setCashierClosingNote: (value: string) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    cashierSessionId,
    actorUserId,
    selectedRuntimeDeviceId,
    closingNote,
    setIsBusy,
    setErrorMessage,
    setCashierSessions,
    setActiveCashierSession,
    setCashierClosingNote,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    await storeControlPlaneClient.closeCashierSession(accessToken, tenantId, branchId, cashierSessionId, {
      closing_note: closingNote || null,
    });
    const response = await storeControlPlaneClient.listCashierSessions(accessToken, tenantId, branchId, 'OPEN');
    const records = resolveCashierSessionRecords(response);
    startTransition(() => {
      setCashierSessions(records);
      setActiveCashierSession(resolveActiveCashierSession(records, selectedRuntimeDeviceId, actorUserId));
      setCashierClosingNote('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to close cashier session');
  } finally {
    setIsBusy(false);
  }
}
