import React from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import Home from '../app/page';

vi.mock('../app/map-panel', () => ({ MapPanel: () => <div>Map placeholder</div> }));
vi.mock('../app/audio-recorder', () => ({ AudioRecorder: () => <button type="button">Start recording</button> }));

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'accepted' }), { status: 202 })));
});
afterEach(cleanup);

test('shows the privacy-first landing page and opens the reporting form', () => {
  render(<Home />);
  expect(screen.getByText('See emerging needs. Verify before acting.')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Submit a report' }));
  expect(screen.getByRole('heading', { name: 'Submit a community report' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Start recording' })).toBeInTheDocument();
});

test('supports report text entry and visible incident filters', () => {
  render(<Home />);
  fireEvent.click(screen.getByRole('button', { name: 'Submit a report' }));
  fireEvent.change(screen.getByPlaceholderText('Maji imeingia kwa nyumba kadhaa karibu na mto...'), { target: { value: 'Flooding reported near homes' } });
  expect(screen.getByDisplayValue('Flooding reported near homes')).toBeInTheDocument();
  expect(screen.getAllByRole('combobox')).toHaveLength(2);
  expect(screen.getByText('All risk levels')).toBeInTheDocument();
});
