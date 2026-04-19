import { StoreThemeProvider } from '@store/ui';
import { PlatformAdminWorkspace } from './control-plane/PlatformAdminWorkspace';

export function App() {
  return (
    <StoreThemeProvider storageKey="platform-admin.theme.mode">
      <PlatformAdminWorkspace />
    </StoreThemeProvider>
  );
}
