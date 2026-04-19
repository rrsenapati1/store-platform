import { PlatformAdminAuthEntrySurface } from './PlatformAdminAuthEntrySurface';
import { PlatformAdminWorkspaceShell } from './PlatformAdminWorkspaceShell';
import { usePlatformAdminWorkspace } from './usePlatformAdminWorkspace';

export function PlatformAdminWorkspace() {
  const workspace = usePlatformAdminWorkspace();

  if (workspace.actor) {
    return <PlatformAdminWorkspaceShell workspace={workspace} />;
  }

  return (
    <PlatformAdminAuthEntrySurface
      errorMessage={workspace.errorMessage}
      isBusy={workspace.isBusy}
      korsenexToken={workspace.korsenexToken}
      onChangeKorsenexToken={workspace.setKorsenexToken}
      onSignIn={workspace.beginSignIn}
      onStartSession={workspace.startSession}
      planCount={workspace.billingPlans.length}
      sessionState={workspace.sessionState}
      showLocalDeveloperControls={Boolean(import.meta.env.DEV)}
      tenantCount={workspace.tenants.length}
    />
  );
}
