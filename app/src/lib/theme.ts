import { createTheme } from '@mantine/core';

export const theme = createTheme({
  primaryColor: 'rdg-orange',
  fontFamily: 'Inter, system-ui, sans-serif',
  fontFamilyMonospace: 'Fira Code, ui-monospace, monospace',
  headings: {
    fontFamily: 'Inter, system-ui, sans-serif',
    fontWeight: '700',
  },
  colors: {
    'rdg-orange': [
      '#FFF7ED',
      '#FFEDD5',
      '#FED7AA',
      '#FDBA74',
      '#FB923C',
      '#F97316',
      '#EA580C',
      '#C2410C',
      '#9A3412',
      '#7C2D12',
    ],
  },
});
