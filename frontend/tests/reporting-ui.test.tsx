import React from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import Home from '../app/page';

vi.mock('../app/audio-recorder', () => ({ AudioRecorder: () => <button type="button">Start recording</button> }));

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'accepted' }), { status: 202 })));
});
afterEach(cleanup);

test('shows a privacy-first public landing page with an anonymous reporting form', () => {
  render(<Home />);
  expect(screen.getByText('Share the event, not your identity.')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'What did you observe?' })).toBeInTheDocument();
  expect(screen.getByText('Zero-Knowledge Privacy Engine Active')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Responder dashboard' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Start recording' })).toBeInTheDocument();
});

test('supports report text entry and a four-domain quick-select control', () => {
  render(<Home />);
  fireEvent.change(screen.getByPlaceholderText('Maji imeingia kwa nyumba kadhaa karibu na mto...'), { target: { value: 'Flooding reported near homes' } });
  expect(screen.getByDisplayValue('Flooding reported near homes')).toBeInTheDocument();
  const electoral=screen.getByRole('button', { name: 'Electoral Tension' });
  fireEvent.click(electoral);
  expect(electoral).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getAllByRole('button', { name: /Emergency|Intimidation|Tension|Dispute/ })).toHaveLength(4);
});
