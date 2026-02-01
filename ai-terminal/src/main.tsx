import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/global.css';

// Note: StrictMode removed to prevent double-mounting which breaks xterm.js
ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
