import urlJoin from 'url-join';
import { encodeUriComponents } from './utils';
import axios, { AxiosInstance } from 'axios';

export const API_PREFIX = 'api';
export const SPAWN_PREFIX = 'spawn';
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
    prefix: 'api' | 'spawn';
    path: string;
    query?: string;
    data?: { [key: string]: any } | FormData;
  }): Promise<T> {
    const { method, path } = args;

    const data = args.data ?? {};
    let url = urlJoin(args.prefix, encodeUriComponents(path));
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
      data
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
