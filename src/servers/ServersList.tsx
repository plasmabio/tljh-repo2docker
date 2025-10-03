import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { memo, useMemo } from 'react';

import { Box } from '@mui/system';
import { IServerData } from './types';
import { formatTime } from '../common/utils';
import { RemoveServerButton } from './RemoveServerButton';
import { OpenServerButton } from './OpenServerButton';
import { IconButton } from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import ClearIcon from '@mui/icons-material/Clear';
const columns: GridColDef[] = [
  {
    field: 'name',
    headerName: 'Server name',
    flex: 1
  },
  {
    field: 'image',
    headerName: 'Image',
    flex: 1
  },
  {
    field: 'last_activity',
    headerName: 'Last activity',
    width: 250
  },
  {
    field: 'active',
    headerName: 'Status',
    width: 125,
    hideSortIcons: true,
    renderCell: params => {
      return params.value ? (
        <IconButton>
          <CheckIcon color="success" />
        </IconButton>
      ) : (
        <IconButton>
          <ClearIcon color="error" />
        </IconButton>
      );
    }
  },
  {
    field: 'status',
    headerName: '',
    width: 175,
    filterable: false,
    sortable: false,
    hideable: false,
    renderCell: params => {
      return <RemoveServerButton server={params.row.name} />;
    }
  },
  {
    field: 'action',
    headerName: '',
    width: 175,
    filterable: false,
    sortable: false,
    hideable: false,
    renderCell: params => {
      return (
        <OpenServerButton
          url={params.row.url}
          serverName={params.row.name}
          imageName={params.row.uid ?? params.row.image}
          active={params.row.active}
        />
      );
    }
  }
];

export interface IServerListProps {
  servers: IServerData[];
  defaultServer: IServerData;
}

function _ServerList(props: IServerListProps) {
  const rows = useMemo(() => {
    let servers = [...props.servers];
    if (props.defaultServer.active) {
      servers = [props.defaultServer, ...servers];
    }
    const allServers = servers.map((it, id) => {
      const newItem: any = { ...it, id };
      newItem.image =
        it?.user_options?.display_name ?? it?.user_options?.image ?? '';
      newItem.uid = it?.user_options?.uid ?? null;
      newItem.last_activity = formatTime(newItem.last_activity);
      return newItem;
    });

    return allServers;
  }, [props]);
  return (
    <Box sx={{ padding: 1 }}>
      <DataGrid
        rows={rows}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 100
            }
          }
        }}
        pageSizeOptions={[100]}
        disableRowSelectionOnClick
        density="compact"
        autoHeight
        slots={{
          noRowsOverlay: () => {
            return (
              <Box sx={{ textAlign: 'center', padding: '25px' }}>
                No servers are running
              </Box>
            );
          }
        }}
      />
    </Box>
  );
}

export const ServerList = memo(_ServerList);
