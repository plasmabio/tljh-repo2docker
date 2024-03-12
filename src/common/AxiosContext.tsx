import { createContext, useContext } from 'react';
import { AxiosClient } from './axiosclient';

export const AxiosContext = createContext<AxiosClient>(new AxiosClient({}));

export const useAxios = () => {
  return useContext(AxiosContext);
};
