import '@fontsource/roboto/300.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';

import { createRoot } from 'react-dom/client';

import { JupyterhubContext } from '../common/JupyterhubContext';
import App, { IAppProps } from './App';

const rootElement = document.getElementById('environments-root');
if (rootElement) {
  const root = createRoot(rootElement);
  const dataElement = document.getElementById('tljh-page-data');
  let configData: IAppProps = {
    images: [],
    default_cpu_limit: '2',
    default_mem_limit: '2G',
    machine_profiles: [],
    node_selector: {},
    use_binderhub: false
  };
  if (dataElement) {
    configData = JSON.parse(dataElement.textContent || '') as IAppProps;
  }
  const jhData = (window as any).jhdata;
  const {
    base_url,
    xsrf_token,
    user,
    hub_prefix,
    service_prefix,
    admin_access
  } = jhData;
  root.render(
    <JupyterhubContext.Provider
      value={{
        baseUrl: base_url,
        xsrfToken: xsrf_token,
        user,
        hubPrefix: hub_prefix ?? base_url,
        servicePrefix: service_prefix ?? base_url,
        adminAccess: admin_access
      }}
    >
      <App {...configData} />
    </JupyterhubContext.Provider>
  );
}
