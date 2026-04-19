import { StoreThemeProvider } from '@store/ui';
import { StoreRuntimeWorkspace } from './control-plane/StoreRuntimeWorkspace';
import { CustomerDisplayRoute, isCustomerDisplayRoute } from './customer-display/customerDisplayRoute';

export function App() {
  if (isCustomerDisplayRoute()) {
    return (
      <StoreThemeProvider storageKey="store-desktop.theme.mode">
        <CustomerDisplayRoute />
      </StoreThemeProvider>
    );
  }

  return (
    <StoreThemeProvider storageKey="store-desktop.theme.mode">
      <StoreRuntimeWorkspace />
    </StoreThemeProvider>
  );
}
