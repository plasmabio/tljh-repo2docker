import ReplayIcon from '@mui/icons-material/Replay';
import { IconButton, Tooltip } from '@mui/material';
import { Fragment, memo, useCallback, useMemo, useState } from 'react';

import { useJupyterhub } from '../common/JupyterhubContext';
import {
  EnvironmentFormDialog,
  IEnvironmentDialogConfigProps,
  IFormValues
} from './NewEnvironmentDialog';
import { IEnvironmentData } from './types';

/**
 * An object from the database (BinderHub), or a Python dict repr from the
 * image label (local, see docker.py). Unreadable means "not set".
 */
function parseNodeSelector(
  raw: IEnvironmentData['node_selector']
): { [key: string]: string } | undefined {
  if (!raw) {
    return undefined;
  }
  if (typeof raw === 'object') {
    return raw;
  }
  for (const text of [raw, raw.replace(/'/g, '"')]) {
    try {
      const parsed = JSON.parse(text);
      if (parsed && typeof parsed === 'object') {
        return parsed;
      }
    } catch {
      // try the next form
    }
  }
  return undefined;
}

interface IRebuildEnvironmentButtonProps extends IEnvironmentDialogConfigProps {
  environment: IEnvironmentData;
  onRefresh?: () => void;
}

function _RebuildEnvironmentButton(props: IRebuildEnvironmentButtonProps) {
  const jhData = useJupyterhub();
  const [open, setOpen] = useState(false);
  const handleOpen = useCallback(() => setOpen(true), []);
  const handleClose = useCallback(() => setOpen(false), []);

  const initialValues = useMemo<Partial<IFormValues>>(
    () => ({
      repo: props.environment.repo,
      ref: props.environment.ref,
      name: props.environment.display_name,
      cpu: props.environment.cpu_limit,
      // mem_limit comes from the Docker label formatted as "<n>G" (see
      // docker.py); the form and backend expect a plain number in GB, so strip
      // the unit suffix to avoid a "Memory Limit must be a number" error.
      memory: props.environment.mem_limit?.replace(/G$/, ''),
      buildargs: props.environment.buildargs,
      provider: props.environment.provider,
      node_selector: parseNodeSelector(props.environment.node_selector)
    }),
    [props.environment]
  );

  if (!props.environment.uid) {
    return null;
  }

  // Only the owner of an environment can rebuild it. Admins viewing others'
  // envs still see the row but not the rebuild action.
  if (props.environment.owner !== jhData.user) {
    return null;
  }

  return (
    <Fragment>
      <Tooltip title="Rebuild environment">
        <IconButton onClick={handleOpen} size="small">
          <ReplayIcon />
        </IconButton>
      </Tooltip>
      {open && (
        <EnvironmentFormDialog
          open={open}
          onClose={handleClose}
          onRefresh={props.onRefresh}
          default_cpu_limit={props.default_cpu_limit}
          default_mem_limit={props.default_mem_limit}
          machine_profiles={props.machine_profiles}
          node_selector={props.node_selector}
          use_binderhub={props.use_binderhub}
          repo_providers={props.repo_providers}
          initialValues={initialValues}
          rebuildUid={props.environment.uid}
        />
      )}
    </Fragment>
  );
}

export const RebuildEnvironmentButton = memo(_RebuildEnvironmentButton);
