import {
  DataGrid,
  GridColDef,
  GridRowSelectionModel,
  GridColumnVisibilityModel
} from '@mui/x-data-grid';
import { IEnvironmentData } from './types';
import { memo, useMemo, useState } from 'react';

import { Box } from '@mui/system';
import { RemoveEnvironmentButton } from './RemoveEnvironmentButton';
import { RebuildEnvironmentButton } from './RebuildEnvironmentButton';
import { EnvironmentLogButton } from './LogDialog';
import {
  IEnvironmentDialogConfigProps,
  IMachineProfile,
  INodeSelector
} from './NewEnvironmentDialog';

export interface IEnvironmentListProps {
  images: IEnvironmentData[];
  default_cpu_limit?: string;
  default_mem_limit?: string;
  machine_profiles?: IMachineProfile[];
  node_selector?: INodeSelector;
  use_binderhub?: boolean;
  repo_providers?: { label: string; value: string }[];
  hideRemoveButton?: boolean;
  hideRebuildButton?: boolean;
  onRefresh?: () => void;
  pageSize?: number;
  selectable?: boolean;
  rowSelectionModel?: GridRowSelectionModel;
  setRowSelectionModel?: (selected: GridRowSelectionModel) => void;
  loading?: boolean;
}

function _EnvironmentList(props: IEnvironmentListProps) {
  // The rebuild button needs the same config as the create dialog; collect it
  // once so the column renderCell below can pass it through.
  const dialogConfig: IEnvironmentDialogConfigProps = useMemo(
    () => ({
      default_cpu_limit: props.default_cpu_limit ?? '2',
      default_mem_limit: props.default_mem_limit ?? '2',
      machine_profiles: props.machine_profiles ?? [],
      node_selector: props.node_selector ?? {},
      use_binderhub: Boolean(props.use_binderhub),
      repo_providers: props.repo_providers
    }),
    [
      props.default_cpu_limit,
      props.default_mem_limit,
      props.machine_profiles,
      props.node_selector,
      props.use_binderhub,
      props.repo_providers
    ]
  );

  const columns: GridColDef[] = useMemo(
    () => [
      {
        field: 'display_name',
        headerName: 'Name',
        flex: 1,
        minWidth: 200
      },
      {
        field: 'repo',
        headerName: 'Repository URL',
        flex: 1,
        minWidth: 100,
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
        width: 130,
        renderCell: params => {
          return (
            <a href={`${params.row.repo}/tree/${params.value}`}>
              {params.value}
            </a>
          );
        }
      },
      {
        field: 'mem_limit',
        headerName: 'Mem. Limit (GB)',
        width: 180
      },
      {
        field: 'cpu_limit',
        headerName: 'CPU Limit',
        width: 130
      },
      {
        field: 'creation_date',
        headerName: 'Creation Date',
        width: 150
      },
      {
        field: 'owner',
        headerName: 'Owner',
        width: 150
      },
      {
        field: 'status',
        headerName: 'Status',
        width: 150,
        hideSortIcons: true,
        renderCell: params => {
          const image = params.row.uid ?? params.row.image_name;
          const name = params.row.display_name;
          if (params.value === 'built') {
            return (
              <EnvironmentLogButton name={name} image={image} status="built" />
            );
          }
          if (params.value === 'building') {
            return (
              <EnvironmentLogButton
                name={name}
                image={image}
                status="building"
              />
            );
          }
          if (params.value === 'failed') {
            return (
              <EnvironmentLogButton name={name} image={image} status="failed" />
            );
          }
          return null;
        }
      },
      {
        field: 'rebuild',
        headerName: '',
        width: 70,
        filterable: false,
        sortable: false,
        hideable: false,
        renderCell: params => {
          const status = params.row.status;
          if (status !== 'built' && status !== 'failed') {
            return null;
          }
          return (
            <RebuildEnvironmentButton
              environment={params.row}
              onRefresh={props.onRefresh}
              {...dialogConfig}
            />
          );
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
              onRefresh={props.onRefresh}
            />
          );
        }
      }
    ],
    [dialogConfig, props.onRefresh]
  );

  const [columnVisibility, setColumnVisibility] =
    useState<GridColumnVisibilityModel>({
      display_name: true,
      repo: true,
      ref: true,
      mem_limit: true,
      cpu_limit: true,
      creation_date: true,
      owner: true,
      status: true,
      rebuild: !props.hideRebuildButton,
      remove: !props.hideRemoveButton
    });

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
        columnVisibilityModel={columnVisibility}
        onColumnVisibilityModelChange={newVisibility =>
          setColumnVisibility(newVisibility)
        }
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
