import { Typography } from '@mui/material';
import Box from '@mui/material/Box';
import { memo, useCallback } from 'react';

import { useAxios } from '../common/AxiosContext';
import { ButtonWithConfirm } from '../common/ButtonWithConfirm';
import { useJupyterhub } from '../common/JupyterhubContext';
import { API_PREFIX } from '../common/axiosclient';

interface IRemoveServerButton {
  server: string;
}

function _RemoveServerButton(props: IRemoveServerButton) {
  const axios = useAxios();
  const jhData = useJupyterhub();
  const removeEnv = useCallback(async () => {
    let path = '';
    if (props.server.length > 0) {
      path = `users/${jhData.user}/servers/${props.server}`;
    } else {
      path = `users/${jhData.user}/server`;
    }
    try {
      await axios.request({
        method: 'delete',
        prefix: API_PREFIX,
        path,
        data: { remove: props.server.length > 0 }
      });
      window.location.reload();
    } catch (e: any) {
      console.error(e);
    }
  }, [props.server, axios, jhData]);

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
