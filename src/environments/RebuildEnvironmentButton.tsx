import ReplayIcon from '@mui/icons-material/Replay';
import { IconButton, Tooltip } from '@mui/material';
import { Fragment, memo, useCallback, useMemo, useState } from 'react';

import {
  EnvironmentFormDialog,
  IEnvironmentDialogConfigProps,
  IFormValues
} from './NewEnvironmentDialog';
import { IEnvironmentData } from './types';

interface IRebuildEnvironmentButtonProps extends IEnvironmentDialogConfigProps {
  environment: IEnvironmentData;
}

function _RebuildEnvironmentButton(props: IRebuildEnvironmentButtonProps) {
  const [open, setOpen] = useState(false);
  const handleOpen = useCallback(() => setOpen(true), []);
  const handleClose = useCallback(() => setOpen(false), []);

  const initialValues = useMemo<Partial<IFormValues>>(
    () => ({
      repo: props.environment.repo,
      ref: props.environment.ref,
      name: props.environment.display_name,
      cpu: props.environment.cpu_limit,
      memory: props.environment.mem_limit,
      buildargs: props.environment.buildargs
    }),
    [props.environment]
  );

  if (!props.environment.uid) {
    return null;
  }

  return (
    <Fragment>
      <Tooltip title="Rebuild environment">
        <IconButton onClick={handleOpen} size="small">
          <ReplayIcon />
        </IconButton>
      </Tooltip>
      <EnvironmentFormDialog
        open={open}
        onClose={handleClose}
        default_cpu_limit={props.default_cpu_limit}
        default_mem_limit={props.default_mem_limit}
        machine_profiles={props.machine_profiles}
        node_selector={props.node_selector}
        use_binderhub={props.use_binderhub}
        repo_providers={props.repo_providers}
        initialValues={initialValues}
        rebuildUid={props.environment.uid}
      />
    </Fragment>
  );
}

export const RebuildEnvironmentButton = memo(_RebuildEnvironmentButton);
