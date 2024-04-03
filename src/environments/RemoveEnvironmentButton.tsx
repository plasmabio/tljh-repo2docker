import { Typography } from '@mui/material';
import Box from '@mui/material/Box';
import { memo, useCallback } from 'react';

import { useAxios } from '../common/AxiosContext';
import { ButtonWithConfirm } from '../common/ButtonWithConfirm';
import { ENV_PREFIX } from './types';

interface IRemoveEnvironmentButton {
  name: string;
  image: string;
}

function _RemoveEnvironmentButton(props: IRemoveEnvironmentButton) {
  const axios = useAxios();

  const removeEnv = useCallback(async () => {
    const response = await axios.serviceClient.request({
      method: 'delete',
      path: ENV_PREFIX,
      data: { name: props.image }
    });
    if (response?.status === 'ok') {
      window.location.reload();
    } else {
      /* */
    }
  }, [props.image, axios]);

  return (
    <ButtonWithConfirm
      buttonLabel="Remove"
      dialogTitle="Remove environment"
      dialogBody={
        <Box>
          <Typography>
            Are you sure you want to remove the following environment?
          </Typography>
          <pre>{props.name}</pre>
        </Box>
      }
      action={removeEnv}
    />
  );
}

export const RemoveEnvironmentButton = memo(_RemoveEnvironmentButton);
