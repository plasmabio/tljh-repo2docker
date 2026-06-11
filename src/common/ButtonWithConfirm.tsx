import { Button, IconButton, Tooltip } from '@mui/material';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import { Fragment, JSX, memo, useCallback, useState } from 'react';
import { Loading } from './LoadingAnimation';

interface IButtonWithConfirm {
  buttonLabel: string;
  dialogTitle: string;
  dialogBody: JSX.Element;
  action: (() => void) | (() => Promise<void>);
  okLabel?: string;
  cancelLabel?: string;
  icon?: JSX.Element;
}

function _ButtonWithConfirm(props: IButtonWithConfirm) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const handleOpen = () => {
    setOpen(true);
  };
  const handleClose = (
    event?: any,
    reason?: 'backdropClick' | 'escapeKeyDown'
  ) => {
    if (reason && reason === 'backdropClick') {
      return;
    }
    setOpen(false);
  };

  const removeEnv = useCallback(async () => {
    setLoading(true);
    try {
      await props.action();
    } finally {
      // Always clear the spinner, otherwise a reused dialog instance (e.g.
      // recycled by the DataGrid) reopens already showing the loading state.
      setLoading(false);
      handleClose();
    }
  }, [props, setLoading]);

  return (
    <Fragment>
      {props.icon ? (
        <Tooltip title={props.buttonLabel}>
          <IconButton onClick={handleOpen} color="error" size="small">
            {props.icon}
          </IconButton>
        </Tooltip>
      ) : (
        <Button onClick={handleOpen} color="error" size="small">
          {props.buttonLabel}
        </Button>
      )}

      <Dialog
        className="tljh-form-dialog"
        open={open}
        onClose={handleClose}
        fullWidth
        maxWidth={'sm'}
      >
        <DialogTitle>{props.dialogTitle}</DialogTitle>
        <DialogContent>
          {!loading && props.dialogBody}
          {loading && <Loading />}
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={handleClose}>
            {props.cancelLabel ?? 'Cancel'}
          </Button>
          <Button variant="contained" color="error" onClick={removeEnv}>
            {props.okLabel ?? 'Accept'}
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  );
}

export const ButtonWithConfirm = memo(_ButtonWithConfirm);
