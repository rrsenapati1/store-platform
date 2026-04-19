import { StoreThemeProvider } from '@store/ui';
import { OwnerWorkspace } from './control-plane/OwnerWorkspace';

export function App() {
  return (
    <StoreThemeProvider storageKey="owner-web.theme.mode">
      <OwnerWorkspace />
    </StoreThemeProvider>
  );
}
