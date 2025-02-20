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
  TextField,
  Typography
} from '@mui/material';
import {
  Fragment,
  memo,
  useCallback,
  useEffect,
  useMemo,
  useState
} from 'react';

import { useAxios } from '../common/AxiosContext';
import { SmallTextField } from '../common/SmallTextField';
import { ENV_PREFIX } from './types';

export interface IMachineProfile {
  label: string;
  cpu: string;
  memory: string;
}
interface INodeSelectorOption {
  description: string;
  values: string[];
}

export interface INodeSelector {
  [key: string]: INodeSelectorOption;
}

export interface INewEnvironmentDialogProps {
  default_cpu_limit: string;
  default_mem_limit: string;
  machine_profiles: IMachineProfile[];
  node_selector: INodeSelector;
  use_binderhub: boolean;
  repo_providers?: { label: string; value: string }[];
}

interface IFormValues {
  provider?: string;
  repo?: string;
  ref?: string;
  name?: string;
  memory?: number;
  cpu?: number;
  buildargs?: string;
  username?: string;
  password?: string;
  node_selector?: { [key: string]: string | undefined };
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
    (
      key: keyof IFormValues,
      value: string | number | { [key: string]: string | undefined }
    ) => {
      setFormValues(old => ({
        ...old,
        [key]: value
      }));
    },
    [setFormValues]
  );
  const validated = useMemo(() => {
    return Boolean(formValues.repo);
  }, [formValues.repo]);

  const [selectedProfile, setSelectedProfile] = useState<number>(0);
  const [selectedProvider, setSelectedProvider] = useState<number>(0);
  const [selectedNodeSelectors, setSelectedNodeSelectors] = useState<{
    [key: string]: string;
  }>(() => {
    const initialSelected: { [key: string]: string } = {};
    Object.entries(props.node_selector).forEach(([key, option]) => {
      initialSelected[key] = option.values[0] || '';
    });
    return initialSelected;
  });

  const onMachineProfileChange = useCallback(
    (value?: string | number) => {
      if (value !== undefined) {
        const index = parseInt(value + '');
        const selected = props.machine_profiles[index];
        if (selected !== undefined) {
          updateFormValue('cpu', selected.cpu + '');
          updateFormValue('memory', selected.memory + '');
          setSelectedProfile(index);
        }
      }
    },
    [props.machine_profiles, updateFormValue]
  );

  const onRepoProviderChange = useCallback(
    (value?: string | number) => {
      if (value !== undefined) {
        const index = parseInt(value + '');
        const selected = props.repo_providers?.[index];
        if (selected !== undefined) {
          updateFormValue('provider', selected.value);
          setSelectedProvider(index);
        }
      }
    },
    [props.repo_providers, updateFormValue]
  );

  const onNodeSelectorChange = useCallback(
    (key: string, value: string) => {
      if (value !== undefined) {
        setSelectedNodeSelectors(prevState => {
          const newState = { ...prevState, [key]: value };
          updateFormValue('node_selector', newState);
          return newState;
        });
      }
    },
    [updateFormValue]
  );

  useEffect(() => {
    if (props.machine_profiles.length > 0) {
      onMachineProfileChange(0);
    }
    if (props.repo_providers && props.repo_providers.length > 0) {
      onRepoProviderChange(0);
    }
    if (props.node_selector) {
      Object.entries(props.node_selector).forEach(([key, option]) => {
        onNodeSelectorChange(key, option.values[0]);
      });
    }
  }, [
    props.machine_profiles,
    props.repo_providers,
    props.node_selector,
    onMachineProfileChange,
    onRepoProviderChange,
    onNodeSelectorChange
  ]);
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
          onChange={e => onMachineProfileChange(e.target.value)}
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
  }, [props.machine_profiles, selectedProfile, onMachineProfileChange]);

  const NodeSelectorDropdown = useMemo(() => {
    return Object.entries(props.node_selector).map(([key, option]) => (
      <FormControl key={key} fullWidth sx={{ marginTop: '8px' }}>
        <TextField
          id={`${key}-select`}
          value={selectedNodeSelectors[key]}
          label={key + option.description && `(${option.description})`}
          size="small"
          select
          onChange={e => onNodeSelectorChange(key, e.target.value)}
        >
          {option.values.map((val: string) => (
            <MenuItem key={val} value={val}>
              {val}
            </MenuItem>
          ))}
        </TextField>
      </FormControl>
    ));
  }, [props.node_selector, selectedNodeSelectors, onNodeSelectorChange]);

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
        maxWidth={'md'}
        className="tljh-form-dialog"
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
            data.ref = data.ref && data.ref.length > 0 ? data.ref : 'HEAD';
            data.cpu = data.cpu ?? '2';
            data.memory = data.memory ?? '2';
            data.username = data.username ?? '';
            data.password = data.password ?? '';
            const response = await axios.serviceClient.request({
              method: 'post',
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
          {props.use_binderhub && props.repo_providers && (
            <FormControl fullWidth sx={{ marginTop: '8px' }}>
              <InputLabel id="git-provider-select-label">
                Repository provider
              </InputLabel>
              <Select
                labelId="git-provider-select-label"
                id="git-provider-select"
                value={selectedProvider}
                label="Repository provider"
                size="small"
                onChange={e => onRepoProviderChange(e.target.value)}
              >
                {props.repo_providers.map((it, idx) => {
                  return (
                    <MenuItem key={idx} value={idx}>
                      {it.label}
                    </MenuItem>
                  );
                })}
              </Select>
            </FormControl>
          )}
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
            required={false}
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
          {props.node_selector && NodeSelectorDropdown}
          {!props.use_binderhub && (
            <Fragment>
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
            </Fragment>
          )}
          {!props.use_binderhub && (
            <Fragment>
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
            </Fragment>
          )}
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
