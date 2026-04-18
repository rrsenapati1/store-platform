import { startTransition } from 'react';
import type { ControlPlaneShiftSession } from '@store/types';
import { storeControlPlaneClient } from './client';

type SetString = (value: string) => void;

function resolveActiveShiftSession(sessions: ControlPlaneShiftSession[]) {
  return sessions.find((session) => session.status === 'OPEN') ?? null;
}

function resolveShiftSessionRecords(
  response: { records?: ControlPlaneShiftSession[] | null },
): ControlPlaneShiftSession[] {
  return Array.isArray(response.records) ? response.records : [];
}

export async function runLoadShiftSessions(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setShiftSessions: (value: ControlPlaneShiftSession[]) => void;
  setActiveShiftSession: (value: ControlPlaneShiftSession | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    setIsBusy,
    setErrorMessage,
    setShiftSessions,
    setActiveShiftSession,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const response = await storeControlPlaneClient.listShiftSessions(accessToken, tenantId, branchId);
    const records = resolveShiftSessionRecords(response);
    startTransition(() => {
      setShiftSessions(records);
      setActiveShiftSession(resolveActiveShiftSession(records));
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load shift sessions');
  } finally {
    setIsBusy(false);
  }
}

export async function runOpenShiftSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  shiftName: string;
  openingNote: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setShiftSessions: (value: ControlPlaneShiftSession[]) => void;
  setActiveShiftSession: (value: ControlPlaneShiftSession | null) => void;
  setShiftName: (value: string) => void;
  setShiftOpeningNote: (value: string) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    shiftName,
    openingNote,
    setIsBusy,
    setErrorMessage,
    setShiftSessions,
    setActiveShiftSession,
    setShiftName,
    setShiftOpeningNote,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const session = await storeControlPlaneClient.createShiftSession(accessToken, tenantId, branchId, {
      shift_name: shiftName,
      opening_note: openingNote || null,
    });
    const response = await storeControlPlaneClient.listShiftSessions(accessToken, tenantId, branchId);
    const records = resolveShiftSessionRecords(response);
    startTransition(() => {
      setShiftSessions(records);
      setActiveShiftSession(resolveActiveShiftSession(records) ?? session);
      setShiftName('');
      setShiftOpeningNote('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to open shift session');
  } finally {
    setIsBusy(false);
  }
}

export async function runCloseShiftSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  shiftSessionId: string;
  closingNote: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setShiftSessions: (value: ControlPlaneShiftSession[]) => void;
  setActiveShiftSession: (value: ControlPlaneShiftSession | null) => void;
  setShiftClosingNote: (value: string) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    shiftSessionId,
    closingNote,
    setIsBusy,
    setErrorMessage,
    setShiftSessions,
    setActiveShiftSession,
    setShiftClosingNote,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    await storeControlPlaneClient.closeShiftSession(accessToken, tenantId, branchId, shiftSessionId, {
      closing_note: closingNote || null,
    });
    const response = await storeControlPlaneClient.listShiftSessions(accessToken, tenantId, branchId);
    const records = resolveShiftSessionRecords(response);
    startTransition(() => {
      setShiftSessions(records);
      setActiveShiftSession(resolveActiveShiftSession(records));
      setShiftClosingNote('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to close shift session');
  } finally {
    setIsBusy(false);
  }
}
