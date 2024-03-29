export const SERVER_PREFIX = 'servers';
export interface IServerData {
  name: string;
  url: string;
  last_activity: string;
  user_options: { image?: string };
  active: boolean;
}
