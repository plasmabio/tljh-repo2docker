import '@fontsource/roboto/300.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';

import { createRoot } from 'react-dom/client';

import { JupyterhubContext } from '../common/JupyterhubContext';
import App, { IAppProps } from './App';

const rootElement = document.getElementById('servers-root');

if (rootElement) {
  const root = createRoot(rootElement);

  const dataElement = document.getElementById('tljh-page-data');
  let configData: IAppProps = {
    images: [],
    server_data: [],
    default_server_data: {
      name: '',
      url: '',
      last_activity: '',
      user_options: {},
      active: false
    },
    allow_named_servers: false,
    named_server_limit_per_user: 0
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
