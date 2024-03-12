import { createTheme } from '@mui/material';
import './style.css';

export const customTheme = createTheme({
  palette: {
    primary: {
      main: '#1976D2' // Change primary color
    },
    secondary: {
      main: '#FF4081' // Change secondary color
    }
  },
  typography: {
    fontSize: 22
  }
});
