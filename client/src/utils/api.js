const API_BASE = 'http://localhost:8000';

export async function uploadCSV(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/jobs/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error('Failed to upload file');
  }

  return res.json();
}

export async function pollJobStatus(jobId, onComplete) {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}/status`);
      const data = await res.json();
      
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(interval);
        onComplete(data);
      }
    } catch (error) {
      console.error('Error polling status:', error);
    }
  }, 2000);
}

export async function getJobResults(jobId) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/results`);
  
  if (!res.ok) {
    throw new Error('Failed to fetch results');
  }

  return res.json();
}
