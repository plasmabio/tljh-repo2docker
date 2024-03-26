import { Button, IconButton } from '@mui/material';
import { Fragment, memo, useCallback, useEffect, useState } from 'react';

import { useAxios } from '../common/AxiosContext';
import { useJupyterhub } from '../common/JupyterhubContext';
import urlJoin from 'url-join';
import SyncIcon from '@mui/icons-material/Sync';
import { SPAWN_PREFIX } from '../common/axiosclient';

interface IOpenServerButton {
  url: string;
  serverName: string;
  imageName: string;
  active: boolean;
}

function _OpenServerButton(props: IOpenServerButton) {
  const axios = useAxios();
  const jhData = useJupyterhub();

  const [progress, setProgress] = useState(0);
  useEffect(() => {
    const { user, hubPrefix, xsrfToken } = jhData;
    let progressUrl = urlJoin(
      hubPrefix,
      'api',
      'users',
      user,
      'servers',
      props.serverName,
      'progress'
    );
    if (xsrfToken) {
      // add xsrf token to url parameter
      const sep = progressUrl.indexOf('?') === -1 ? '?' : '&';
      progressUrl = progressUrl + sep + '_xsrf=' + xsrfToken;
    }

    const eventSource = new EventSource(progressUrl);
    eventSource.onerror = err => {
      setProgress(100);
      eventSource.close();
    };

    eventSource.onmessage = event => {
      const data = JSON.parse(event.data);

      setProgress(data.progress ?? 0);
    };
  }, [jhData, setProgress, props.serverName]);

  const createServer = useCallback(async () => {
    const imageName = props.imageName;
    const data = new FormData();
    data.append('image', imageName);
    try {
      await axios.hubClient.request({
        method: 'post',
        prefix: SPAWN_PREFIX,
        path: `${jhData.user}/${props.serverName}`,
        data
      });
      window.open(props.url, '_blank')?.focus();
      window.location.reload();
    } catch (e: any) {
      console.error(e);
    }
  }, [props, axios, jhData]);

  return (
    <Fragment>
      {progress === 100 && (
        <Fragment>
          {props.active && (
            <Button href={props.url} target="_blank">
              Open Server
            </Button>
          )}

          {!props.active && (
            <Button onClick={createServer}>Launch server</Button>
          )}
        </Fragment>
      )}
      {progress < 100 && (
        <IconButton title="Starting">
          <SyncIcon
            sx={{
              animation: 'spin 2s linear infinite',
              '@keyframes spin': {
                '0%': {
                  transform: 'rotate(360deg)'
                },
                '100%': {
                  transform: 'rotate(0deg)'
                }
              }
            }}
            htmlColor="orange"
          />
        </IconButton>
      )}
    </Fragment>
  );
}

export const OpenServerButton = memo(_OpenServerButton);
