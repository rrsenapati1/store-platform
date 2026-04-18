import { startTransition } from 'react';
import type { ControlPlaneAttendanceSession } from '@store/types';
import { storeControlPlaneClient } from './client';

type SetString = (value: string) => void;

function resolveActiveAttendanceSession(
  sessions: ControlPlaneAttendanceSession[],
  selectedRuntimeDeviceId: string,
  actorUserId: string,
) {
  return sessions.find((session) => (
    session.status === 'OPEN'
    && session.device_registration_id === selectedRuntimeDeviceId
    && session.runtime_user_id === actorUserId
  )) ?? null;
}

function resolveAttendanceSessionRecords(
  response: { records?: ControlPlaneAttendanceSession[] | null },
): ControlPlaneAttendanceSession[] {
  return Array.isArray(response.records) ? response.records : [];
}

export async function runLoadAttendanceSessions(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  actorUserId: string;
  selectedRuntimeDeviceId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setAttendanceSessions: (value: ControlPlaneAttendanceSession[]) => void;
  setActiveAttendanceSession: (value: ControlPlaneAttendanceSession | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    actorUserId,
    selectedRuntimeDeviceId,
    setIsBusy,
    setErrorMessage,
    setAttendanceSessions,
    setActiveAttendanceSession,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const response = await storeControlPlaneClient.listAttendanceSessions(accessToken, tenantId, branchId);
    const records = resolveAttendanceSessionRecords(response);
    startTransition(() => {
      setAttendanceSessions(records);
      setActiveAttendanceSession(resolveActiveAttendanceSession(records, selectedRuntimeDeviceId, actorUserId));
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load attendance sessions');
  } finally {
    setIsBusy(false);
  }
}

export async function runOpenAttendanceSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  deviceRegistrationId: string;
  staffProfileId: string;
  clockInNote: string;
  actorUserId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setAttendanceSessions: (value: ControlPlaneAttendanceSession[]) => void;
  setActiveAttendanceSession: (value: ControlPlaneAttendanceSession | null) => void;
  setAttendanceClockInNote: (value: string) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    deviceRegistrationId,
    staffProfileId,
    clockInNote,
    actorUserId,
    setIsBusy,
    setErrorMessage,
    setAttendanceSessions,
    setActiveAttendanceSession,
    setAttendanceClockInNote,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const attendanceSession = await storeControlPlaneClient.createAttendanceSession(accessToken, tenantId, branchId, {
      device_registration_id: deviceRegistrationId,
      staff_profile_id: staffProfileId,
      clock_in_note: clockInNote || null,
    });
    const response = await storeControlPlaneClient.listAttendanceSessions(accessToken, tenantId, branchId);
    const records = resolveAttendanceSessionRecords(response);
    startTransition(() => {
      setAttendanceSessions(records);
      setActiveAttendanceSession(resolveActiveAttendanceSession(records, deviceRegistrationId, actorUserId) ?? attendanceSession);
      setAttendanceClockInNote('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to clock in');
  } finally {
    setIsBusy(false);
  }
}

export async function runCloseAttendanceSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  attendanceSessionId: string;
  actorUserId: string;
  selectedRuntimeDeviceId: string;
  clockOutNote: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setAttendanceSessions: (value: ControlPlaneAttendanceSession[]) => void;
  setActiveAttendanceSession: (value: ControlPlaneAttendanceSession | null) => void;
  setAttendanceClockOutNote: (value: string) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    attendanceSessionId,
    actorUserId,
    selectedRuntimeDeviceId,
    clockOutNote,
    setIsBusy,
    setErrorMessage,
    setAttendanceSessions,
    setActiveAttendanceSession,
    setAttendanceClockOutNote,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    await storeControlPlaneClient.closeAttendanceSession(accessToken, tenantId, branchId, attendanceSessionId, {
      clock_out_note: clockOutNote || null,
    });
    const response = await storeControlPlaneClient.listAttendanceSessions(accessToken, tenantId, branchId);
    const records = resolveAttendanceSessionRecords(response);
    startTransition(() => {
      setAttendanceSessions(records);
      setActiveAttendanceSession(resolveActiveAttendanceSession(records, selectedRuntimeDeviceId, actorUserId));
      setAttendanceClockOutNote('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to clock out');
  } finally {
    setIsBusy(false);
  }
}
