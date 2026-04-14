/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';
import { App } from '../App';

describe('store runtime shell identity', () => {
  test('shows browser shell identity posture before a runtime session starts', async () => {
    render(<App />);

    expect(await screen.findByText('Shell identity')).toBeInTheDocument();
    expect(screen.getByText('Browser web runtime')).toBeInTheDocument();
    expect(screen.getByText('localhost')).toBeInTheDocument();
  });
});
