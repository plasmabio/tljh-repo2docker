import { createContext, useContext } from 'react';

export interface IJupyterhubData {
  baseUrl: string;
  prefix: string;
  user: string;
  adminAccess: boolean;
  xsrfToken: string;
}
export const JupyterhubContext = createContext<IJupyterhubData>({
  baseUrl: '',
  prefix: '',
  user: '',
  adminAccess: false,
  xsrfToken: ''
});

export const useJupyterhub = () => {
  return useContext(JupyterhubContext);
};
