import { Stack } from '@mui/material';
import ScopedCssBaseline from '@mui/material/ScopedCssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { useEffect, useMemo, useState } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import { IServerData, SERVER_PREFIX } from './types';
import Backdrop from '@mui/material/Backdrop';
import { AxiosContext, useAxios } from '../common/AxiosContext';
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
  const axios = useAxios();
  const [themeMode, setThemeMode] = useState<'light' | 'dark'>(
    (document.documentElement.getAttribute('data-bs-theme') as
      | 'light'
      | 'dark') || 'light'
  );
  const [loading, setLoading] = useState(false);
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

  useEffect(() => {
    (async () => {
      const query = new URL(window.location.href).searchParams;
      const requestServerName = query.get('name');
      const requestEnv = query.get('environment');
      if (!requestServerName) {
        return;
      }

      setLoading(true);

      const allServers = Object.fromEntries(
        props.server_data.map(item => [item.name, item])
      );
      const allImages = Object.fromEntries(
        props.images.map(item => [item.display_name, item])
      );

      const server = allServers[requestServerName];
      const startServer = async (imageKey: string) => {
        const imageData = allImages[imageKey];
        if (!imageData) {
          setLoading(false);
          alert(`Environment ${imageKey} does not exist`);
          return;
        }
        const imageName = imageData.uid ?? imageData.image_name;
        const data = {
          imageName,
          userName: jhData.user,
          serverName: requestServerName
        };

        try {
          await axios.serviceClient.request({
            method: 'post',
            path: SERVER_PREFIX,
            data
          });
          window.location.reload();
        } catch (e: any) {
          setLoading(false);
          alert(e);
        }
      };

      if (server) {
        if (server.active) {
          window.location.replace(server.url);
        } else {
          const imageDisplayName = server.user_options?.display_name;
          if (!imageDisplayName) {
            setLoading(false);
            alert('Missing image name');
            return;
          }
          await startServer(imageDisplayName);
        }
      } else if (requestEnv) {
        await startServer(requestEnv);
      }

      setLoading(false);
    })();
  }, [axios, jhData, props.server_data, props.images]);

  return (
    <ThemeProvider theme={customTheme}>
      <AxiosContext.Provider value={{ serviceClient }}>
        <ScopedCssBaseline>
          <Backdrop
            sx={{ color: '#fff', zIndex: theme => theme.zIndex.drawer + 1 }}
            open={loading}
          >
            <CircularProgress size={'100px'} />
          </Backdrop>

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
