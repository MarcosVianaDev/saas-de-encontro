import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';

function App() {
  const [status, setStatus] = useState('Verificando backend...');
  useEffect(() => {
    fetch('/api/health/').then(async response => {
      if (!response.ok) throw new Error('Backend indisponivel');
      const data = await response.json();
      setStatus(`Django ${data.django}, PostgreSQL e Redis funcionando.`);
    }).catch(() => setStatus('Backend indisponivel. Consulte os logs do Docker.'));
  }, []);
  return <main><h1>SaaS de Encontro</h1><p>Ambiente de desenvolvimento iniciado.</p><p>{status}</p></main>;
}

createRoot(document.getElementById('root')!).render(<App />);
