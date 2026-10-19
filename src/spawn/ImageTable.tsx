import { useEffect, useState } from 'react';
import { useTheme } from '@mui/material/styles';
import {
  DataGrid,
  GridColDef,
  GridColumnVisibilityModel,
  GridRowsProp
} from '@mui/x-data-grid';
import {
  Box,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Button,
  useMediaQuery
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
  const theme = useTheme();
  // On narrow screens, keep the room for the display name: the limits and
  // the creation date are still shown in the info dialog.
  const isMedium = useMediaQuery(theme.breakpoints.down('md'));
  const isSmall = useMediaQuery(theme.breakpoints.down('sm'));
  // Controlled so that a breakpoint change resets it, while the columns
  // panel can still toggle columns in between.
  const [columnVisibilityModel, setColumnVisibilityModel] =
    useState<GridColumnVisibilityModel>({});
  useEffect(() => {
    setColumnVisibilityModel({
      mem_limit: !isMedium,
      cpu_limit: !isMedium,
      creation_date: !isSmall
    });
  }, [isMedium, isSmall]);
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
        color: theme.palette.primary.main
      }}
    >
      {icon}
      {text}
    </button>
  );

  const columns: GridColDef[] = [
    {
      field: 'action',
      headerName: '',
      width: isMedium ? 76 : 120,
      align: 'center',
      renderCell: params =>
        renderButton(
          <PlayCircleIcon
            style={{ fontSize: 28, marginRight: isMedium ? 0 : '8px' }}
          />,
          e => handleStartServer(e, params.row.display_name, params.row.ref),
          isMedium ? '' : 'Start'
        ),
      disableColumnMenu: true,
      hideable: false,
      sortable: false,
      filterable: false,
      editable: false
    },
    {
      field: 'display_name',
      headerName: 'Display Name',
      flex: 1,
      minWidth: 150,
      headerClassName: 'bold-header'
    },
    { field: 'mem_limit', headerName: 'Memory Limit', width: 170 },
    { field: 'cpu_limit', headerName: 'CPU Limit', width: 140 },
    { field: 'creation_date', headerName: 'Creation Date', width: 220 },
    {
      field: 'info',
      headerName: '',
      width: 60,
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
          <InfoIcon
            style={{ fontSize: 22, color: theme.palette.primary.main }}
          />
        </button>
      ),
      disableColumnMenu: true,
      hideable: false,
      sortable: false,
      filterable: false,
      editable: false
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
      console.error('Image name and ref are required');
    }
  };

  return (
    <Box sx={{ padding: 1 }}>
      <DataGrid
        rows={rowsFormatted}
        columns={columns}
        columnVisibilityModel={columnVisibilityModel}
        onColumnVisibilityModelChange={setColumnVisibilityModel}
        // the button only reverts the changes made since the panel opened
        localeText={{ columnsManagementReset: 'Cancel' }}
        slotProps={{
          columnsManagement: {
            getTogglableColumns: columns =>
              columns.filter(col => col.hideable).map(col => col.field)
          }
        }}
        disableRowSelectionOnClick
        sx={{
          '& .MuiDataGrid-columnHeader': {
            backgroundColor: theme.palette.action.hover
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
            backgroundColor: theme.palette.action.hover
          },
          '& .MuiDataGrid-row:nth-of-type(even)': {
            backgroundColor: theme.palette.action.selected
          }
        }}
      />

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>
          <strong>Image Informations</strong>
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
                  style={{
                    color: theme.palette.primary.main,
                    textDecoration: 'underline'
                  }}
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
              <p>
                <strong>Memory Limit:</strong> {imageInfo.mem_limit}
              </p>
              <p>
                <strong>CPU Limit:</strong> {imageInfo.cpu_limit}
              </p>
              <p>
                <strong>Creation Date:</strong> {imageInfo.creation_date}
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
