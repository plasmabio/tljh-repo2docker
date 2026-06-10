import DeleteIcon from '@mui/icons-material/Delete';
import { Typography } from '@mui/material';
import Box from '@mui/material/Box';
import { memo, useCallback } from 'react';

import { useAxios } from '../common/AxiosContext';
import { ButtonWithConfirm } from '../common/ButtonWithConfirm';
import { ENV_PREFIX } from './types';

interface IRemoveEnvironmentButton {
  name: string;
  image: string;
  onRefresh?: () => void;
}

function _RemoveEnvironmentButton(props: IRemoveEnvironmentButton) {
  const { image, onRefresh } = props;
  const axios = useAxios();

  const removeEnv = useCallback(async () => {
    const response = await axios.serviceClient.request({
      method: 'delete',
      path: ENV_PREFIX,
      data: { name: image }
    });
    if (response?.status === 200) {
      onRefresh?.();
    } else {
      console.error(response);
    }
  }, [image, onRefresh, axios]);

  return (
    <ButtonWithConfirm
      buttonLabel="Remove environment"
      icon={<DeleteIcon />}
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
