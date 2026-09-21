import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { AudioRecorder } from '../app/audio-recorder';

test('explains when microphone permission is unavailable', async () => {
  render(<AudioRecorder onReady={vi.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: /Record/ }));
  await waitFor(() => expect(screen.getByText('Microphone access was not granted. You can submit a text report instead.')).toBeInTheDocument());
});
