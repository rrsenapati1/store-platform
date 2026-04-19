/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';
import { App } from '../App';

describe('store runtime shell identity', () => {
  test('shows the entry screen and bootstrap posture before a runtime session starts', async () => {
    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Store access' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Entry' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getAllByText(/Resolving runtime shell|Browser web runtime/).length).toBeGreaterThan(0);
    expect(screen.getByText('localhost')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start runtime session' })).toBeInTheDocument();
  });
});
