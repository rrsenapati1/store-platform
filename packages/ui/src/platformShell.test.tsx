/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { PlatformCommandHeader, PlatformCommandShell, PlatformExceptionBoard, PlatformNavRail, PlatformPanel, PlatformSignalRow } from './platformShell';

describe('platform shell primitives', () => {
  test('renders navigation, header, signals, and exceptions', () => {
    const onSelect = vi.fn();

    render(
      <PlatformCommandShell
        navRail={(
          <PlatformNavRail
            title="Korsenex Platform"
            subtitle="Control tower"
            items={[
              { id: 'overview', label: 'Overview' },
              { id: 'release', label: 'Release' },
            ]}
            activeItemId="overview"
            onSelect={onSelect}
          />
        )}
        commandHeader={(
          <PlatformCommandHeader
            title="Overview"
            environmentLabel="staging"
            releaseLabel="2026.04.19"
            statusLabel="Healthy"
            statusTone="success"
          />
        )}
      >
        <PlatformSignalRow
          items={[
            { label: 'Release readiness', value: 'Healthy', tone: 'success' },
            { label: 'Operations', value: '0 degraded', tone: 'success' },
          ]}
        />
        <PlatformPanel title="Critical exceptions">
          <PlatformExceptionBoard
            items={[
              {
                id: '1',
                title: 'Dead-letter jobs',
                detail: '1 jobs require review.',
                tone: 'danger',
              },
            ]}
          />
        </PlatformPanel>
      </PlatformCommandShell>,
    );

    expect(screen.getByText('Korsenex Platform')).toBeInTheDocument();
    expect(screen.getByText('Env: staging')).toBeInTheDocument();
    expect(screen.getByText('Release readiness')).toBeInTheDocument();
    expect(screen.getByText('Dead-letter jobs')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Release' }));
    expect(onSelect).toHaveBeenCalledWith('release');
  });
});
