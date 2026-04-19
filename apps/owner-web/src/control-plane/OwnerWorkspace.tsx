import { OwnerAuthEntrySurface } from './OwnerAuthEntrySurface';
import { OwnerWorkspaceShell } from './OwnerWorkspaceShell';
import { useOwnerWorkspace } from './useOwnerWorkspace';

export function OwnerWorkspace() {
  const workspace = useOwnerWorkspace();

  if (workspace.actor) {
    return <OwnerWorkspaceShell workspace={workspace} />;
  }

  return (
    <OwnerAuthEntrySurface
      branchCount={workspace.branches.length}
      errorMessage={workspace.errorMessage}
      isBusy={workspace.isBusy}
      korsenexToken={workspace.korsenexToken}
      onboardingStatus={workspace.tenant?.onboarding_status}
      onChangeKorsenexToken={workspace.setKorsenexToken}
      onSignIn={workspace.beginSignIn}
      onStartSession={workspace.startSession}
      sessionState={workspace.sessionState}
      showLocalDeveloperControls={Boolean(import.meta.env.DEV)}
    />
  );
}
