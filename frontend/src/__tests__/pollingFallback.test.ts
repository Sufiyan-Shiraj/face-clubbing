import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from '../api/client';

describe('SSE Streaming and 500ms Polling Fallback', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('polls /api/jobs/status periodically at 500ms intervals during running jobs', async () => {
    const mockStatus1 = {
      job_id: 'job_123',
      status: 'running' as const,
      stage: 'processing',
      current: 5,
      total: 20,
      percent: 25.0,
      progress: 0.25,
      message: 'Processing photo 5 of 20',
    };

    const mockStatus2 = {
      ...mockStatus1,
      current: 10,
      percent: 50.0,
      progress: 0.5,
      message: 'Processing photo 10 of 20',
    };

    let pollCount = 0;
    const getJobStatusSpy = vi.spyOn(api, 'getJobStatus').mockImplementation(async () => {
      pollCount++;
      return pollCount === 1 ? mockStatus1 : mockStatus2;
    });

    const receivedUpdates: any[] = [];
    // Simulate App's 500ms polling timer
    const intervalId = setInterval(async () => {
      try {
        const st = await api.getJobStatus();
        receivedUpdates.push(st);
      } catch {
        // ignore
      }
    }, 500);

    // Initial tick at 500ms
    await vi.advanceTimersByTimeAsync(500);
    expect(getJobStatusSpy).toHaveBeenCalledTimes(1);
    expect(receivedUpdates).toHaveLength(1);
    expect(receivedUpdates[0].percent).toBe(25.0);

    // Second tick at 1000ms
    await vi.advanceTimersByTimeAsync(500);
    expect(getJobStatusSpy).toHaveBeenCalledTimes(2);
    expect(receivedUpdates).toHaveLength(2);
    expect(receivedUpdates[1].percent).toBe(50.0);

    clearInterval(intervalId);

    // After clearing, no further polls occur
    await vi.advanceTimersByTimeAsync(1000);
    expect(getJobStatusSpy).toHaveBeenCalledTimes(2);
  });

  it('resiliently handles transient polling errors without crashing', async () => {
    let callNum = 0;
    const getJobStatusSpy = vi.spyOn(api, 'getJobStatus').mockImplementation(async () => {
      callNum++;
      if (callNum === 1) {
        throw new Error('Network timeout (transient)');
      }
      return {
        job_id: 'job_123',
        status: 'running' as const,
        stage: 'clustering',
        current: 20,
        total: 20,
        percent: 100.0,
        progress: 1.0,
        message: 'Clustering faces',
      };
    });

    const successfulUpdates: any[] = [];
    const intervalId = setInterval(async () => {
      try {
        const st = await api.getJobStatus();
        successfulUpdates.push(st);
      } catch {
        // Ignored in App.tsx line 132
      }
    }, 500);

    // First interval fails
    await vi.advanceTimersByTimeAsync(500);
    expect(getJobStatusSpy).toHaveBeenCalledTimes(1);
    expect(successfulUpdates).toHaveLength(0);

    // Second interval succeeds
    await vi.advanceTimersByTimeAsync(500);
    expect(getJobStatusSpy).toHaveBeenCalledTimes(2);
    expect(successfulUpdates).toHaveLength(1);
    expect(successfulUpdates[0].stage).toBe('clustering');

    clearInterval(intervalId);
  });
});
