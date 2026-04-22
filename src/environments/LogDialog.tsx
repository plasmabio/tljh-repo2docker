import 'xterm/css/xterm.css';

import CheckIcon from '@mui/icons-material/Check';
import ErrorIcon from '@mui/icons-material/Error';
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
  status?: 'building' | 'failed' | 'built';
}

const terminalFactory = () => {
  const terminal = new Terminal({ convertEol: true, disableStdin: true });
  const fitAddon = new FitAddon();
  terminal.loadAddon(fitAddon);
  return { terminal, fitAddon };
};

function _EnvironmentLogButton(props: IEnvironmentLogButton) {
  const jhData = useJupyterhub();
  const status = props.status ?? 'building';
  const [open, setOpen] = useState(false);
  const [buildResult, setBuildResult] = useState<'built' | 'failed' | null>(
    null
  );
  const divRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<{ terminal: Terminal; fitAddon: FitAddon }>(
    terminalFactory()
  );
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  const handleOpen = useCallback(() => {
    setOpen(true);
    if (divRef.current) {
      const { terminal, fitAddon } = terminalFactory();
      terminalRef.current.terminal = terminal;
      terminalRef.current.fitAddon = fitAddon;

      terminal.open(divRef.current);
      fitAddon.fit();

      resizeObserverRef.current = new ResizeObserver(() => {
        fitAddon.fit();
      });
      resizeObserverRef.current.observe(divRef.current);

      const { servicePrefix, xsrfToken } = jhData;

      let logsUrl = urlJoin(
        servicePrefix,
        'api',
        'environments',
        props.image,
        'logs'
      );
      if (xsrfToken) {
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
          setBuildResult('built');
          return;
        }
        if (data.phase === 'error') {
          eventSource.close();
          setBuildResult('failed');
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

    resizeObserverRef.current?.disconnect();
    resizeObserverRef.current = null;

    setOpen(false);
  };

  const effectiveStatus = buildResult ?? status;
  const dialogTitle =
    effectiveStatus === 'failed'
      ? `Build failed: ${props.name}`
      : effectiveStatus === 'built'
        ? `Build logs: ${props.name}`
        : `Creating environment ${props.name}`;

  const triggerButton =
    effectiveStatus === 'failed' ? (
      <IconButton onClick={handleOpen} title="View error logs">
        <ErrorIcon color="error" />
      </IconButton>
    ) : effectiveStatus === 'built' ? (
      <IconButton onClick={handleOpen} title="View build logs">
        <CheckIcon color="success" />
      </IconButton>
    ) : (
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
    );

  return (
    <Fragment>
      {triggerButton}
      <Dialog
        open={open}
        onClose={handleClose}
        fullWidth
        keepMounted={true}
        className="tljh-form-dialog"
        PaperProps={{
          sx: {
            width: theme => theme.breakpoints.values.lg,
            maxWidth: '90vw',
            height: '80vh',
            resize: 'both',
            overflow: 'auto',
            display: 'flex',
            flexDirection: 'column'
          }
        }}
      >
        <DialogTitle>{dialogTitle}</DialogTitle>
        <DialogContent
          sx={{
            flex: 1,
            display: 'flex',
            overflow: 'hidden',
            padding: 0
          }}
        >
          <div
            ref={divRef}
            style={{
              flex: 1,
              width: '100%',
              height: '100%'
            }}
          />
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
