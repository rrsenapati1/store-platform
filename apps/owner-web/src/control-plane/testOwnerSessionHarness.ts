import { render, screen } from '@testing-library/react';
import type { ReactElement } from 'react';

const OWNER_BOOTSTRAP_HASH = '#stub_sub=owner-1&stub_email=owner@acme.local&stub_name=Acme%20Owner';

export async function renderOwnerWithSession(element: ReactElement, path = '/'): Promise<void> {
  window.history.replaceState(null, '', `${path}${OWNER_BOOTSTRAP_HASH}`);
  render(element);
  await screen.findByText('Acme Owner', {}, { timeout: 10_000 });
}
