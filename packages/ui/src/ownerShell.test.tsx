/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import {
  OwnerCommandHeader,
  OwnerCommandShell,
  OwnerExceptionBoard,
  OwnerNavRail,
  OwnerPanel,
  OwnerSignalRow,
} from './ownerShell';

describe('owner shell primitives', () => {
  test('renders navigation, command header, signals, and exception board', () => {
    const onSelect = vi.fn();
    const onBranchChange = vi.fn();

    render(
      <OwnerCommandShell
        navRail={
          <OwnerNavRail
            title="Acme Retail"
            subtitle="Owner console"
            items={[
              { id: 'overview', label: 'Overview' },
              { id: 'operations', label: 'Operations' },
            ]}
            activeItemId="overview"
            onSelect={onSelect}
          />
        }
        commandHeader={
          <OwnerCommandHeader
            title="Overview"
            subtitle="What needs attention right now"
            branchOptions={[
              { value: 'all', label: 'All branches' },
              { value: 'branch-1', label: 'Bengaluru Flagship' },
            ]}
            selectedBranch="all"
            onBranchChange={onBranchChange}
          />
        }
      >
        <OwnerSignalRow
          items={[
            { label: 'Sales posture', value: 'Healthy' },
            { label: 'Returns', value: '2 pending', tone: 'warning' },
          ]}
        />
        <OwnerPanel title="Exceptions">
          <OwnerExceptionBoard
            items={[
              { id: 'exception-1', title: 'Low stock in Bengaluru Flagship', detail: 'Classic Tea below reorder point' },
            ]}
          />
        </OwnerPanel>
      </OwnerCommandShell>,
    );

    expect(screen.getByText('Acme Retail')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Overview' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByText('What needs attention right now')).toBeInTheDocument();
    expect(screen.getByLabelText('Branch filter')).toHaveValue('all');
    expect(screen.getByText('Sales posture')).toBeInTheDocument();
    expect(screen.getByText('Low stock in Bengaluru Flagship')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Operations' }));
    expect(onSelect).toHaveBeenCalledWith('operations');

    fireEvent.change(screen.getByLabelText('Branch filter'), { target: { value: 'branch-1' } });
    expect(onBranchChange).toHaveBeenCalledWith('branch-1');
  });
});
