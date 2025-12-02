import { IconButton } from '@mui/material';
import { DataGrid, GridColDef, GridRowSelectionModel } from '@mui/x-data-grid';
import { IEnvironmentData } from './types';
import { memo, useMemo } from 'react';
import CheckIcon from '@mui/icons-material/Check';

import { Box } from '@mui/system';
import { RemoveEnvironmentButton } from './RemoveEnvironmentButton';
import { EnvironmentLogButton } from './LogDialog';

const columns: GridColDef[] = [
  {
    field: 'display_name',
    headerName: 'Name',
    flex: 1
  },
  {
    field: 'repo',
    headerName: 'Repository URL',
    flex: 1,
    renderCell: params => {
      return (
        <a title={params.value} href={params.value} target="_blank">
          {params.value}
        </a>
      );
    }
  },
  {
    field: 'ref',
    headerName: 'Reference',
    width: 200,
    renderCell: params => {
      return (
        <a href={`${params.row.repo}/tree/${params.value}`}>{params.value}</a>
      );
    }
  },
  {
    field: 'mem_limit',
    headerName: 'Mem. Limit (GB)',
    width: 200
  },
  {
    field: 'cpu_limit',
    headerName: 'CPU Limit',
    width: 150
  },
  {
    field: 'status',
    headerName: 'Status',
    width: 150,
    hideSortIcons: true,
    renderCell: params => {
      return params.value === 'built' ? (
        <IconButton>
          <CheckIcon color="success" />
        </IconButton>
      ) : params.value === 'building' ? (
        <EnvironmentLogButton
          name={params.row.display_name}
          image={params.row.uid ?? params.row.image_name}
        />
      ) : null;
    }
  },
  {
    field: 'remove',
    headerName: '',
    width: 100,
    filterable: false,
    sortable: false,
    hideable: false,
    renderCell: params => {
      return (
        <RemoveEnvironmentButton
          name={params.row.display_name}
          image={params.row.uid ?? params.row.image_name}
        />
      );
    }
  }
];

export interface IEnvironmentListProps {
  images: IEnvironmentData[];
  default_cpu_limit?: string;
  default_mem_limit?: string;
  hideRemoveButton?: boolean;
  pageSize?: number;
  selectable?: boolean;
  rowSelectionModel?: GridRowSelectionModel;
  setRowSelectionModel?: (selected: GridRowSelectionModel) => void;
  loading?: boolean;
}

function _EnvironmentList(props: IEnvironmentListProps) {
  const rows = useMemo(() => {
    return props.images.map((it, id) => {
      const newItem = { ...it, id };
      newItem.cpu_limit =
        newItem.cpu_limit.length > 0
          ? newItem.cpu_limit
          : (props.default_cpu_limit ?? '2');
      newItem.mem_limit =
        newItem.mem_limit.length > 0
          ? newItem.mem_limit
          : (props.default_mem_limit ?? '2');
      return newItem;
    });
  }, [props]);
  return (
    <Box sx={{ padding: 1 }}>
      <DataGrid
        loading={Boolean(props.loading)}
        rows={rows}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: props.pageSize ?? 100
            }
          }
        }}
        pageSizeOptions={[props.pageSize ?? 100]}
        disableRowSelectionOnClick={!props.selectable}
        sx={{
          '& .MuiDataGrid-virtualScroller::-webkit-scrollbar': {
            overflow: rows.length > 0 ? 'auto' : 'hidden'
          }
        }}
        columnVisibilityModel={{ remove: !props.hideRemoveButton }}
        checkboxSelection={Boolean(props.selectable)}
        rowSelectionModel={props.rowSelectionModel}
        onRowSelectionModelChange={props.setRowSelectionModel}
        density="compact"
        autoHeight
        slots={{
          noRowsOverlay: () => {
            return (
              <Box sx={{ textAlign: 'center', padding: '25px' }}>
                No environment available
              </Box>
            );
          }
        }}
      />
    </Box>
  );
}

export const EnvironmentList = memo(_EnvironmentList);
