import { Stack } from '@mui/material';
import ScopedCssBaseline from '@mui/material/ScopedCssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';

import { IEnvironmentData } from './types';
import { EnvironmentList } from './EnvironmentList';
import {
  IMachineProfile,
  INodeSelector,
  NewEnvironmentDialog
} from './NewEnvironmentDialog';
import { AxiosContext } from '../common/AxiosContext';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AxiosClient } from '../common/axiosclient';
import { useJupyterhub } from '../common/JupyterhubContext';
import { ENV_PREFIX } from './types';
import '../common/style.css';

const ENV_POLL_INTERVAL_MS = 5000;

export interface IAppProps {
  images: IEnvironmentData[];
  default_cpu_limit: string;
  default_mem_limit: string;
  machine_profiles: IMachineProfile[];
  node_selector: INodeSelector;
  use_binderhub: boolean;
  repo_providers?: { label: string; value: string }[];
}
export default function App(props: IAppProps) {
  const jhData = useJupyterhub();

  const [images, setImages] = useState<IEnvironmentData[]>(props.images);

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

  // Auto-refresh: poll the JSON listing so admins see BUILDING → BUILT
  // transitions and other admins' create/delete actions without a manual
  // reload. The Refresh button stays as an explicit escape hatch.
  const inFlight = useRef(false);
  const refresh = useCallback(async () => {
    if (inFlight.current) {
      return;
    }
    inFlight.current = true;
    try {
      const response = await serviceClient.request<{
        images: IEnvironmentData[];
      }>({
        method: 'get',
        path: ENV_PREFIX
      });
      if (response?.status === 200 && Array.isArray(response.data?.images)) {
        setImages(response.data.images);
      }
    } catch (err) {
      console.warn('Failed to refresh environments list', err);
    } finally {
      inFlight.current = false;
    }
  }, [serviceClient]);

  useEffect(() => {
    const tick = () => {
      if (document.visibilityState === 'visible') {
        void refresh();
      }
    };
    const id = window.setInterval(tick, ENV_POLL_INTERVAL_MS);
    return () => window.clearInterval(id);
  }, [refresh]);

  return (
    <ThemeProvider theme={customTheme}>
      <AxiosContext.Provider value={{ serviceClient }}>
        <ScopedCssBaseline>
          <Stack sx={{ padding: 1 }} spacing={1}>
            <NewEnvironmentDialog
              default_cpu_limit={props.default_cpu_limit}
              default_mem_limit={props.default_mem_limit}
              machine_profiles={props.machine_profiles}
              node_selector={props.node_selector}
              use_binderhub={props.use_binderhub}
              repo_providers={props.repo_providers}
              onRefresh={refresh}
            />
            <EnvironmentList {...props} images={images} onRefresh={refresh} />
          </Stack>
        </ScopedCssBaseline>
      </AxiosContext.Provider>
    </ThemeProvider>
  );
}
