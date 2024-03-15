import { createContext, useContext } from 'react';

export interface IJupyterhubData {
  baseUrl: string;
  servicePrefix: string;
  hubPrefix: string;
  user: string;
  adminAccess: boolean;
  xsrfToken: string;
}
export const JupyterhubContext = createContext<IJupyterhubData>({
  baseUrl: '',
  servicePrefix: '',
  hubPrefix: '',
  user: '',
  adminAccess: false,
  xsrfToken: ''
});

export const useJupyterhub = () => {
  return useContext(JupyterhubContext);
};
