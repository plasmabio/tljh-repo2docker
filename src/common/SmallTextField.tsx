import { TextField, inputLabelClasses } from '@mui/material';
import { styled } from '@mui/material/styles';

export const SmallTextField = styled(TextField)(`
  .${inputLabelClasses.root} {
    font-size: 1.4rem;
  }
`);
