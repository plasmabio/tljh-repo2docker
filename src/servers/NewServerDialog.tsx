import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  OutlinedTextFieldProps
} from '@mui/material';
import { GridRowSelectionModel } from '@mui/x-data-grid';
import { Fragment, memo, useCallback, useMemo, useState } from 'react';

import { EnvironmentList } from '../environments/EnvironmentList';
import { IEnvironmentData } from '../environments/types';
import { SmallTextField } from '../common/SmallTextField';

import { useAxios } from '../common/AxiosContext';
import { SPAWN_PREFIX } from '../common/axiosclient';
import { useJupyterhub } from '../common/JupyterhubContext';
export interface INewServerDialogProps {
  images: IEnvironmentData[];
  allowNamedServers: boolean;
  defaultRunning: boolean;
  serverLimit: number;
}

const commonInputProps: OutlinedTextFieldProps = {
  autoFocus: true,
  required: true,
  margin: 'dense',
  fullWidth: true,
  variant: 'outlined'
};
function _NewServerDialog(props: INewServerDialogProps) {
  const axios = useAxios();
  const jhData = useJupyterhub();
  const [open, setOpen] = useState(false);
  const [serverName, setServerName] = useState<string>('');
  const handleOpen = () => {
    setOpen(true);
  };
  const handleClose = (
    event?: any,
    reason?: 'backdropClick' | 'escapeKeyDown'
  ) => {
    if (reason && reason === 'backdropClick') {
      return;
    }
    setOpen(false);
  };

  const [rowSelectionModel, setRowSelectionModel] =
    useState<GridRowSelectionModel>([]);
  const updateSelectedRow = useCallback(
    (selected: GridRowSelectionModel) => {
      if (selected.length > 1) {
        setRowSelectionModel([selected[selected.length - 1]]);
      } else {
        setRowSelectionModel(selected);
      }
    },
    [setRowSelectionModel]
  );

  const createServer = useCallback(async () => {
    const imageName = props.images[rowSelectionModel[0] as number].image_name;
    const data = new FormData();
    data.append('image', imageName);
    let path = '';
    if (serverName.length > 0) {
      path = `${jhData.user}/${serverName}`;
    } else {
      path = jhData.user;
    }
    try {
      await axios.hubClient.request({
        method: 'post',
        prefix: SPAWN_PREFIX,
        path,
        data
      });
      window.location.reload();
    } catch (e: any) {
      console.error(e);
    }
  }, [serverName, rowSelectionModel, props.images, axios, jhData]);
  const disabled = useMemo(() => {
    if (rowSelectionModel.length === 0) {
      return true;
    }
    if (serverName.length === 0) {
      if (props.defaultRunning) {
        return true;
      } else {
        return false;
      }
    }
  }, [rowSelectionModel, serverName, props.defaultRunning]);
  return (
    <Fragment>
      <Box sx={{ display: 'flex', flexDirection: 'row-reverse' }}>
        <Button onClick={handleOpen} variant="contained">
          Create new Server
        </Button>
      </Box>
      <Dialog open={open} onClose={handleClose} fullWidth maxWidth={'md'}>
        <DialogTitle>Server Options</DialogTitle>
        <DialogContent>
          {props.allowNamedServers && (
            <Box sx={{ padding: 1 }}>
              <SmallTextField
                {...commonInputProps}
                id="server_name"
                name="server_name"
                label="Server name"
                type="string"
                required={false}
                helperText="If empty, a default server will be created"
                onChange={e => setServerName(e.target.value)}
                value={serverName}
                disabled={!props.allowNamedServers}
              />
            </Box>
          )}
          <DialogContentText>Select an environment</DialogContentText>
          <EnvironmentList
            images={props.images}
            hideRemoveButton={true}
            pageSize={10}
            selectable
            rowSelectionModel={rowSelectionModel}
            setRowSelectionModel={updateSelectedRow}
          />
        </DialogContent>
        <DialogActions>
          <Button variant="contained" color="error" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="primary"
            disabled={disabled}
            onClick={createServer}
          >
            Create Server
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  );
}

export const NewServerDialog = memo(_NewServerDialog);
