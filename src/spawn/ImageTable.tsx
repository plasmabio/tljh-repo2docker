import { useState } from 'react';
import { DataGrid, GridColDef, GridRowsProp } from '@mui/x-data-grid';
import {
  Box,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Button
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import PlayCircleIcon from '@mui/icons-material/PlayCircle';

interface IImage {
  id: string;
  display_name: string;
  repo: string;
  ref: string;
  mem_limit: string;
  cpu_limit: string;
  creation_date: string;
  owner: string;
}

const ImageTable: React.FC<{ rows: IImage[] }> = ({ rows }) => {
  const [openDialog, setOpenDialog] = useState(false);
  const [imageInfo, setImageInfo] = useState<IImage | null>(null);

  const handleOpenDialog = (e: React.MouseEvent, image: IImage) => {
    e.preventDefault();
    setImageInfo(image);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setImageInfo(null);
  };

  const renderButton = (
    icon: JSX.Element,
    onClick: (e: React.MouseEvent) => void,
    text: string
  ) => (
    <button
      onClick={onClick}
      style={{
        background: 'transparent',
        border: 'none',
        cursor: 'pointer',
        padding: '6px 12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#1976d2'
      }}
    >
      {icon}
      {text}
    </button>
  );

  const columns: GridColDef[] = [
    {
      field: 'display_name',
      headerName: 'Display Name',
      width: 280,
      headerClassName: 'bold-header'
    },
    { field: 'mem_limit', headerName: 'Memory Limit', width: 180 },
    { field: 'cpu_limit', headerName: 'CPU Limit', width: 150 },
    { field: 'creation_date', headerName: 'Creation Date', width: 150 },
    {
      field: 'info',
      headerName: '',
      width: 80,
      align: 'center',
      renderCell: params => (
        <button
          className="btn btn-sm"
          onClick={e => handleOpenDialog(e, params.row)}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          <InfoIcon style={{ fontSize: 20, color: '#1976d2' }} />
        </button>
      )
    },
    {
      field: 'action',
      headerName: '',
      flex: 1,
      align: 'center',
      renderCell: params =>
        renderButton(
          <PlayCircleIcon style={{ fontSize: 18, marginRight: '8px' }} />,
          e => handleStartServer(e, params.row.display_name, params.row.ref),
          'Start'
        )
    }
  ];

  const rowsFormatted: GridRowsProp = rows.map(image => ({
    ...image,
    id: image.display_name
  }));

  const handleStartServer = async (
    e: React.MouseEvent,
    imageName: string,
    imageRef: string
  ) => {
    e.preventDefault();
    if (imageName && imageRef) {
      try {
        const imageParam = `${imageName}:${imageRef}`;
        await fetch(`/hub/spawn?image=${imageParam}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        window.location.reload();
      } catch (error) {
        console.error('Error starting the server:', error);
      }
    } else {
      console.error('IImage name and ref are required');
    }
  };

  return (
    <Box sx={{ padding: 1 }}>
      <DataGrid
        rows={rowsFormatted}
        columns={columns}
        disableRowSelectionOnClick
        sx={{
          '& .MuiDataGrid-columnHeader': {
            backgroundColor: '#f7f7f7'
          },
          '& .MuiDataGrid-columnHeaderTitle': {
            fontWeight: 'bold',
            fontSize: '20px'
          },
          '& .MuiDataGrid-cell': {
            fontSize: '18px',
            padding: '12px',
            display: 'flex',
            alignItems: 'center'
          },
          '& .MuiDataGrid-row:hover': {
            backgroundColor: '#f5f5f5'
          },
          '& .MuiDataGrid-row:nth-child(even)': {
            backgroundColor: '#fafafa'
          }
        }}
      />

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>
          <strong>IImage Informations</strong>
        </DialogTitle>
        <DialogContent>
          {imageInfo && (
            <div>
              <p>
                <strong>Name:</strong> {imageInfo.display_name}
              </p>
              <p>
                <strong>Repo: </strong>
                <a
                  href={imageInfo.repo}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: '#1976d2', textDecoration: 'underline' }}
                >
                  {imageInfo.repo}
                </a>
              </p>
              <p>
                <strong>Reference:</strong> {imageInfo.ref}
              </p>
              <p>
                <strong>Owner:</strong> {imageInfo.owner}
              </p>
            </div>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ImageTable;
