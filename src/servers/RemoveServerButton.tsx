import { Typography } from '@mui/material';
import Box from '@mui/material/Box';
import { memo, useCallback } from 'react';

import { useAxios } from '../common/AxiosContext';
import { ButtonWithConfirm } from '../common/ButtonWithConfirm';
import { useJupyterhub } from '../common/JupyterhubContext';
import { SERVER_PREFIX } from './types';

interface IRemoveServerButton {
  server: string;
}

function _RemoveServerButton(props: IRemoveServerButton) {
  const axios = useAxios();
  const jhData = useJupyterhub();
  const removeEnv = useCallback(async () => {
    try {
      await axios.serviceClient.request({
        method: 'delete',
        path: SERVER_PREFIX,
        data: {
          userName: jhData.user,
          serverName: props.server
        }
      });
      window.location.reload();
    } catch (e: any) {
      console.error(e);
    }
  }, [props.server, axios, jhData.user]);

  return (
    <ButtonWithConfirm
      buttonLabel="Stop Server"
      dialogTitle="Stop Server"
      dialogBody={
        props.server.length > 0 ? (
          <Box>
            <Typography>
              Are you sure you want to stop the following server?
            </Typography>
            <pre>{props.server}</pre>
          </Box>
        ) : (
          <Box>
            <Typography>
              Are you sure you want to stop the default server?
            </Typography>
          </Box>
        )
      }
      action={removeEnv}
    />
  );
}

export const RemoveServerButton = memo(_RemoveServerButton);
