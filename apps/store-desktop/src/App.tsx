import { StoreRuntimeWorkspace } from './control-plane/StoreRuntimeWorkspace';
import { CustomerDisplayRoute, isCustomerDisplayRoute } from './customer-display/customerDisplayRoute';

export function App() {
  if (isCustomerDisplayRoute()) {
    return <CustomerDisplayRoute />;
  }

  return <StoreRuntimeWorkspace />;
}
