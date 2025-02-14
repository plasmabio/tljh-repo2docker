import { Button } from '@mui/material';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import { Fragment, memo, useCallback, useState } from 'react';
import { Loading } from './LoadingAnimation';

interface IButtonWithConfirm {
  buttonLabel: string;
  dialogTitle: string;
  dialogBody: JSX.Element;
  action: (() => void) | (() => Promise<void>);
  okLabel?: string;
  cancelLabel?: string;
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
    await props.action();
    handleClose();
  }, [props, setLoading]);

  return (
    <Fragment>
      <Button onClick={handleOpen} color="error" size="small">
        {props.buttonLabel}
      </Button>

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
