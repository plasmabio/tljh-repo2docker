import { Stack } from '@mui/material';
import ScopedCssBaseline from '@mui/material/ScopedCssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { useEffect, useMemo, useState } from 'react';

import { IServerData } from './types';
import { AxiosContext } from '../common/AxiosContext';
import { AxiosClient } from '../common/axiosclient';
import { ServerList } from './ServersList';
import { NewServerDialog } from './NewServerDialog';
import { IEnvironmentData } from '../environments/types';
import { useJupyterhub } from '../common/JupyterhubContext';
import '../common/style.css';

export interface IAppProps {
  images: IEnvironmentData[];
  server_data: IServerData[];
  default_server_data: IServerData;
  allow_named_servers: boolean;
  named_server_limit_per_user: number;
}
export default function App(props: IAppProps) {
  const jhData = useJupyterhub();

  const [themeMode, setThemeMode] = useState<'light' | 'dark'>(
    (document.documentElement.getAttribute('data-bs-theme') as
      | 'light'
      | 'dark') || 'light'
  );

  useEffect(() => {
    const observer = new MutationObserver(() => {
      const newTheme = document.documentElement.getAttribute(
        'data-bs-theme'
      ) as 'light' | 'dark';
      if (newTheme !== themeMode) {
        setThemeMode(newTheme);
      }
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-bs-theme']
    });

    return () => observer.disconnect();
  }, [themeMode]);

  // Create theme dynamically based on mode
  const customTheme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: themeMode,
          primary: { main: '#1976D2' },
          secondary: { main: '#FF4081' }
        },
        typography: { fontSize: 22 }
      }),
    [themeMode]
  );

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
