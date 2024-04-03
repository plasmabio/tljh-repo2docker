import { Stack } from '@mui/material';
import ScopedCssBaseline from '@mui/material/ScopedCssBaseline';
import { ThemeProvider } from '@mui/material/styles';

import { customTheme } from '../common/theme';
import { IServerData } from './types';
import { AxiosContext } from '../common/AxiosContext';
import { useMemo } from 'react';
import { AxiosClient } from '../common/axiosclient';
import { ServerList } from './ServersList';
import { NewServerDialog } from './NewServerDialog';
import { IEnvironmentData } from '../environments/types';
import { useJupyterhub } from '../common/JupyterhubContext';

export interface IAppProps {
  images: IEnvironmentData[];
  server_data: IServerData[];
  default_server_data: IServerData;
  allow_named_servers: boolean;
  named_server_limit_per_user: number;
}
export default function App(props: IAppProps) {
  const jhData = useJupyterhub();

  const serviceClient = useMemo(() => {
    const baseUrl = jhData.servicePrefix;
    const xsrfToken = jhData.xsrfToken;
    return new AxiosClient({ baseUrl, xsrfToken });
  }, [jhData]);

  return (
    <ThemeProvider theme={customTheme}>
      <AxiosContext.Provider value={{ serviceClient }}>
        <ScopedCssBaseline>
          <Stack sx={{ padding: 1 }} spacing={1}>
            <NewServerDialog
              images={props.images}
              allowNamedServers={props.allow_named_servers}
              serverLimit={props.named_server_limit_per_user}
              defaultRunning={props.default_server_data.active}
            />
            <ServerList
              servers={props.server_data}
              defaultServer={props.default_server_data}
            />
          </Stack>
        </ScopedCssBaseline>
      </AxiosContext.Provider>
    </ThemeProvider>
  );
}
