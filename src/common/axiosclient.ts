import urlJoin from 'url-join';
import { encodeUriComponents } from './utils';
import axios, { AxiosInstance } from 'axios';

export class AxiosClient {
  constructor(options: AxiosClient.IOptions) {
    this._baseUrl = options.baseUrl ?? '';
    this._xsrfToken = options.xsrfToken;
    this._axios = axios.create({
      baseURL: this._baseUrl
    });
  }

  async request<T = any>(args: {
    method: 'get' | 'post' | 'put' | 'option' | 'delete';
    path: string;
    query?: string;
    data?: { [key: string]: any } | FormData;
    params?: { [key: string]: string };
  }): Promise<T> {
    const { method, path, params } = args;
    const prefix = 'api';
    const data = args.data ?? {};
    let url = urlJoin(prefix, encodeUriComponents(path));
    if (args.query) {
      const sep = url.indexOf('?') === -1 ? '?' : '&';
      url = `${url}${sep}${args.query}`;
    }
    if (this._xsrfToken) {
      const sep = url.indexOf('?') === -1 ? '?' : '&';
      url = `${url}${sep}_xsrf=${this._xsrfToken}`;
    }
    const response = await this._axios.request<T>({
      method,
      url,
      data,
      params
    });
    return response.data;
  }

  private _baseUrl: string;
  private _xsrfToken?: string;
  private _axios: AxiosInstance;
}

export namespace AxiosClient {
  export interface IOptions {
    baseUrl?: string;
    xsrfToken?: string;
  }
}
