import { createTheme, ThemeProvider, useMediaQuery } from '@mui/material';
import ReactDOM from 'react-dom/client';
import ImageTable from './ImageTable';

const imageList = (window as any).imageList || [];

function App() {
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)');
  const theme = createTheme({
    palette: { mode: prefersDark ? 'dark' : 'light' }
  });
  return (
    <ThemeProvider theme={theme}>
      <ImageTable rows={imageList} />
    </ThemeProvider>
  );
}

const container = document.getElementById('image-table-container');
if (container) {
  const root = ReactDOM.createRoot(container);
  root.render(<App />);
} else {
  console.error("Element with id 'image-table-container' not found.");
}
