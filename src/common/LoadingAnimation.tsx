import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
export const Loading = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center' }}>
    <CircularProgress />
  </Box>
);
