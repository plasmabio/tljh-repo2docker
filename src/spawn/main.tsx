import ReactDOM from 'react-dom/client';
import ImageTable from './ImageTable';

const imageList = (window as any).imageList || [];

const container = document.getElementById('image-table-container');
if (container) {
  const root = ReactDOM.createRoot(container);
  root.render(<ImageTable rows={imageList} />);
} else {
  console.error("Element with id 'image-table-container' not found.");
}
