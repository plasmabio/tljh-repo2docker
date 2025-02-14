import 'xterm/css/xterm.css';

import CheckIcon from '@mui/icons-material/Check';
import SyncIcon from '@mui/icons-material/Sync';
import { Button, IconButton } from '@mui/material';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import { Fragment, memo, useCallback, useRef, useState } from 'react';
import urlJoin from 'url-join';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { useJupyterhub } from '../common/JupyterhubContext';

interface IEnvironmentLogButton {
  name: string;
  image: string;
}

const terminalFactory = () => {
  const terminal = new Terminal({ convertEol: true, disableStdin: true });
  const fitAddon = new FitAddon();
  terminal.loadAddon(fitAddon);
  return { terminal, fitAddon };
};

function _EnvironmentLogButton(props: IEnvironmentLogButton) {
  const jhData = useJupyterhub();
  const [open, setOpen] = useState(false);
  const [built, setBuilt] = useState(false);
  const divRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<{ terminal: Terminal; fitAddon: FitAddon }>(
    terminalFactory()
  );
  const handleOpen = useCallback(() => {
    setOpen(true);
    if (divRef.current) {
      const { terminal, fitAddon } = terminalFactory();
      terminalRef.current.terminal = terminal;
      terminalRef.current.fitAddon = fitAddon;

      terminal.open(divRef.current);
      fitAddon.fit();
      const { servicePrefix, xsrfToken } = jhData;

      let logsUrl = urlJoin(
        servicePrefix,
        'api',
        'environments',
        props.image,
        'logs'
      );
      if (xsrfToken) {
        // add xsrf token to url parameter
        const sep = logsUrl.indexOf('?') === -1 ? '?' : '&';
        logsUrl = logsUrl + sep + '_xsrf=' + xsrfToken;
      }
      const eventSource = new EventSource(logsUrl);
      eventSource.onerror = err => {
        console.error('Failed to construct event stream', err);
        eventSource.close();
      };

      eventSource.onmessage = event => {
        const data = JSON.parse(event.data);

        terminal.write(data.message);
        fitAddon.fit();
        if (data.phase === 'built') {
          eventSource.close();
          setBuilt(true);
          return;
        }
      };
    }
  }, [jhData, props.image]);
  const handleClose = (
    event?: any,
    reason?: 'backdropClick' | 'escapeKeyDown'
  ) => {
    if (reason && reason === 'backdropClick') {
      return;
    }

    terminalRef.current.terminal.dispose();
    if (divRef.current) {
      divRef.current.innerHTML = '';
    }
    setOpen(false);
  };

  return (
    <Fragment>
      {!built && (
        <IconButton onClick={handleOpen}>
          <SyncIcon
            sx={{
              animation: 'spin 2s linear infinite',
              '@keyframes spin': {
                '0%': {
                  transform: 'rotate(360deg)'
                },
                '100%': {
                  transform: 'rotate(0deg)'
                }
              }
            }}
            htmlColor="orange"
          />
        </IconButton>
      )}
      {built && (
        <IconButton>
          <CheckIcon color="success" />
        </IconButton>
      )}
      <Dialog
        open={open}
        onClose={handleClose}
        fullWidth
        maxWidth={'lg'}
        keepMounted={true}
        className="tljh-form-dialog"
      >
        <DialogTitle>Creating environment {props.name}</DialogTitle>
        <DialogContent>
          <div ref={divRef} />
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={handleClose}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  );
}

export const EnvironmentLogButton = memo(_EnvironmentLogButton);
