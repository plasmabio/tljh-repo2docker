import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  OutlinedTextFieldProps,
  Select,
  Typography
} from '@mui/material';
import { Fragment, memo, useCallback, useMemo, useState } from 'react';

import { API_PREFIX } from '../common/axiosclient';
import { useAxios } from '../common/AxiosContext';
import { SmallTextField } from '../common/SmallTextField';
import { ENV_PREFIX } from './types';

export interface IMachineProfile {
  label: string;
  cpu: string;
  memory: string;
}
export interface INewEnvironmentDialogProps {
  default_cpu_limit: string;
  default_mem_limit: string;
  machine_profiles: IMachineProfile[];
}

interface IFormValues {
  repo?: string;
  ref?: string;
  name?: string;
  memory?: number;
  cpu?: number;
  buildargs?: string;
  username?: string;
  password?: string;
}
const commonInputProps: OutlinedTextFieldProps = {
  autoFocus: true,
  required: true,
  margin: 'dense',
  fullWidth: true,
  variant: 'outlined'
};

function _NewEnvironmentDialog(props: INewEnvironmentDialogProps) {
  const axios = useAxios();
  const [open, setOpen] = useState(false);
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

  const [formValues, setFormValues] = useState<IFormValues>({});
  const updateFormValue = useCallback(
    (key: keyof IFormValues, value: string | number) => {
      setFormValues(old => {
        return { ...old, [key]: value };
      });
    },
    [setFormValues]
  );
  const validated = useMemo(() => {
    return Boolean(formValues.repo) && Boolean(formValues.ref);
  }, [formValues]);

  const [selectedProfile, setSelectedProfile] = useState<number>(0);

  const MemoryCpuSelector = useMemo(() => {
    return (
      <Fragment>
        <SmallTextField
          {...commonInputProps}
          id="mem_limit"
          name="mem_limit"
          label="Memory limit (GB)"
          size="small"
          type="number"
          helperText="If empty, defaults to 2 GB"
          required={false}
          onChange={e => updateFormValue('memory', e.target.value)}
        />
        <SmallTextField
          {...commonInputProps}
          id="cpu_limit"
          name="cpu_limit"
          size="small"
          label="CPU limit (number of cores)"
          type="number"
          helperText="If empty, defaults to 2 cores"
          required={false}
          onChange={e => updateFormValue('cpu', e.target.value)}
        />
      </Fragment>
    );
  }, [updateFormValue]);

  const MachineProfileSelector = useMemo(() => {
    return (
      <FormControl fullWidth sx={{ marginTop: '8px' }}>
        <InputLabel id="machine-profiles-select-label">
          Machine profile
        </InputLabel>
        <Select
          labelId="machine-profiles-select-label"
          id="machine-profiles-select"
          value={selectedProfile}
          label="Machine profile"
          size="small"
          onChange={e => {
            const value = e.target.value;
            if (value) {
              const index = parseInt(value + '');
              const selected = props.machine_profiles[index];
              updateFormValue('cpu', selected.cpu + '');
              updateFormValue('memory', selected.memory + '');
              setSelectedProfile(index);
            }
          }}
        >
          {props.machine_profiles.map((it, idx) => {
            return (
              <MenuItem key={idx} value={idx}>
                {it.label} ({it.cpu} CPU - {it.memory}G Memory)
              </MenuItem>
            );
          })}
        </Select>
      </FormControl>
    );
  }, [updateFormValue, props.machine_profiles, selectedProfile]);
  return (
    <Fragment>
      <Box sx={{ display: 'flex', flexDirection: 'row-reverse' }}>
        <Button onClick={handleOpen} variant="contained">
          Create new environment
        </Button>
      </Box>
      <Dialog
        open={open}
        onClose={handleClose}
        fullWidth
        maxWidth={'sm'}
        PaperProps={{
          component: 'form',
          onSubmit: async (event: React.FormEvent<HTMLFormElement>) => {
            event.preventDefault();
            const data: any = { ...formValues };
            data.repo = data.repo.trim();
            data.name =
              data.name ??
              (data.repo as string)
                .replace('http://', '')
                .replace('https://', '')
                .replace(/\//g, '-')
                .replace(/\./g, '-');
            data.cpu = data.cpu ?? '2';
            data.memory = data.memory ?? '2';
            data.username = data.username ?? '';
            data.password = data.password ?? '';
            const response = await axios.request({
              method: 'post',
              prefix: API_PREFIX,
              path: ENV_PREFIX,
              data
            });
            if (response?.status === 'ok') {
              window.location.reload();
            } else {
              handleClose();
            }
          }
        }}
      >
        <DialogTitle>Create a new environment</DialogTitle>
        <DialogContent>
          <SmallTextField
            {...commonInputProps}
            id="repo"
            size="small"
            name="repo"
            label="Repository URL"
            type="text"
            onChange={e => updateFormValue('repo', e.target.value)}
            value={formValues.repo ?? ''}
          />
          <SmallTextField
            {...commonInputProps}
            id="ref"
            name="ref"
            size="small"
            label="Reference (git commit)"
            type="text"
            placeholder="HEAD"
            onChange={e => updateFormValue('ref', e.target.value)}
            value={formValues.ref ?? ''}
          />
          <SmallTextField
            {...commonInputProps}
            id="name"
            name="name"
            size="small"
            label="Environment name"
            type="text"
            required={false}
            placeholder="Example: course-python-101-B37"
            onChange={e => updateFormValue('name', e.target.value)}
          />
          {props.machine_profiles.length > 0
            ? MachineProfileSelector
            : MemoryCpuSelector}
          <Divider
            variant="fullWidth"
            textAlign="left"
            sx={{ marginTop: '6px' }}
          >
            <Typography sx={{ fontWeight: 500, fontSize: '1.4rem' }}>
              Advanced
            </Typography>
          </Divider>
          <SmallTextField
            {...commonInputProps}
            id="build_args"
            name="build_args"
            label="Build arguments"
            type="text"
            size="small"
            multiline
            rows={4}
            required={false}
            placeholder="Build arguments in the form of arg1=val1..."
            onChange={e => updateFormValue('buildargs', e.target.value)}
          />
          <Divider
            variant="fullWidth"
            textAlign="left"
            sx={{ marginTop: '6px' }}
          >
            <Typography sx={{ fontWeight: 500, fontSize: '1.4rem' }}>
              Credentials
            </Typography>
          </Divider>
          <SmallTextField
            {...commonInputProps}
            id="git_user"
            name="git_user"
            size="small"
            label="Git user name"
            type="text"
            required={false}
            onChange={e => updateFormValue('username', e.target.value)}
          />
          <SmallTextField
            {...commonInputProps}
            id="git_password"
            name="git_password"
            size="small"
            label="Git password"
            type="password"
            required={false}
          />
        </DialogContent>
        <DialogActions>
          <Button variant="contained" color="error" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="primary"
            disabled={!validated}
            type="submit"
          >
            Create Environment
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  );
}

export const NewEnvironmentDialog = memo(_NewEnvironmentDialog);
