import { Stack } from '@mui/material';
import ScopedCssBaseline from '@mui/material/ScopedCssBaseline';
import { ThemeProvider } from '@mui/material/styles';

import { customTheme } from '../common/theme';
import { IEnvironmentData } from './types';
import { EnvironmentList } from './EnvironmentList';
import { IMachineProfile, NewEnvironmentDialog } from './NewEnvironmentDialog';
import { AxiosContext } from '../common/AxiosContext';
import { useMemo } from 'react';
import { AxiosClient } from '../common/axiosclient';
import { useJupyterhub } from '../common/JupyterhubContext';

export interface IAppProps {
  images: IEnvironmentData[];
  default_cpu_limit: string;
  default_mem_limit: string;
  machine_profiles: IMachineProfile[];
}
export default function App(props: IAppProps) {
  const jhData = useJupyterhub();

  const hubClient = useMemo(() => {
    const baseUrl = jhData.hubPrefix;
    const xsrfToken = jhData.xsrfToken;
    return new AxiosClient({ baseUrl, xsrfToken });
  }, [jhData]);

  const serviceClient = useMemo(() => {
    const baseUrl = jhData.servicePrefix;
    const xsrfToken = jhData.xsrfToken;
    return new AxiosClient({ baseUrl, xsrfToken });
  }, [jhData]);

  return (
    <ThemeProvider theme={customTheme}>
      <AxiosContext.Provider value={{ hubClient, serviceClient }}>
        <ScopedCssBaseline>
          <Stack sx={{ padding: 1 }} spacing={1}>
            <NewEnvironmentDialog
              default_cpu_limit={props.default_cpu_limit}
              default_mem_limit={props.default_mem_limit}
              machine_profiles={props.machine_profiles}
            />
            <EnvironmentList {...props} />
          </Stack>
        </ScopedCssBaseline>
      </AxiosContext.Provider>
    </ThemeProvider>
  );
}
