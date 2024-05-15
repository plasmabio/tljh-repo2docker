import { Button } from '@mui/material';
import { Fragment, memo, useCallback, useMemo } from 'react';

import { useAxios } from '../common/AxiosContext';
import { useJupyterhub } from '../common/JupyterhubContext';
import { SERVER_PREFIX } from './types';

interface IOpenServerButton {
  url: string;
  serverName: string;
  imageName: string;
  active: boolean;
}

function _OpenServerButton(props: IOpenServerButton) {
  const axios = useAxios();
  const jhData = useJupyterhub();

  const createServer = useCallback(async () => {
    const imageName = props.imageName;
    const data = {
      imageName,
      userName: jhData.user,
      serverName: props.serverName
    };
    try {
      await axios.serviceClient.request({
        method: 'post',
        path: SERVER_PREFIX,
        data
      });
      window.open(props.url, '_blank')?.focus();
      window.location.reload();
    } catch (e: any) {
      console.error(e);
    }
  }, [props, axios, jhData]);

  const pendingUrl = useMemo(() => {
    const url = props.url.replace('user', 'hub/spawn-pending');
    return url.endsWith('/') ? url.slice(0, -1) : url;
  }, [props.url]);
  return (
    <Fragment>
      {props.active && (
        <Button href={pendingUrl} target="_blank">
          Open Server
        </Button>
      )}

      {!props.active && <Button onClick={createServer}>Launch server</Button>}
    </Fragment>
  );
}

export const OpenServerButton = memo(_OpenServerButton);
