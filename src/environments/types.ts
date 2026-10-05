export const ENV_PREFIX = 'environments';
export interface IEnvironmentData {
  image_name: string;
  cpu_limit: string;
  display_name: string;
  creation_date: string;
  owner: string;
  mem_limit: string;
  ref: string;
  repo: string;
  status: string;
  uid?: string;
  buildargs?: string;
  // BinderHub backend only, absent on entries built before it was stored.
  provider?: string;
  // An object from the DB (BinderHub backend), a serialized string from the
  // Docker label (local backend).
  node_selector?: { [key: string]: string } | string;
}
