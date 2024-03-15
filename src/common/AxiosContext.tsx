import { createContext, useContext } from 'react';
import { AxiosClient } from './axiosclient';

export const AxiosContext = createContext<{
  hubClient: AxiosClient;
  serviceClient: AxiosClient;
}>({ hubClient: new AxiosClient({}), serviceClient: new AxiosClient({}) });

export const useAxios = () => {
  return useContext(AxiosContext);
};
