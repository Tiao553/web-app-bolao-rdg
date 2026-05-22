import { Box, Group, Text } from '@mantine/core';

type BrandLogoProps = {
  size?: 'sm' | 'lg';
};

export function BrandLogo({ size = 'sm' }: BrandLogoProps) {
  const isLg = size === 'lg';

  return (
    <Group gap={isLg ? 12 : 8} wrap="nowrap">
      <Box
        style={{
          width: isLg ? 48 : 30,
          height: isLg ? 48 : 30,
          background: 'var(--mantine-color-rdg-orange-5)',
          borderRadius: isLg ? 10 : 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <Text
          fw={800}
          c="white"
          size={isLg ? 'lg' : 'xs'}
          style={{ letterSpacing: '-0.02em', lineHeight: 1 }}
        >
          RDG
        </Text>
      </Box>
      <Box>
        <Text fw={600} size={isLg ? 'xl' : 'sm'} lh={1}>
          Copa RDG
        </Text>
        <Text
          size="xs"
          c="rdg-orange"
          ff="monospace"
          style={{ letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 2, lineHeight: 1 }}
        >
          Rei do Gado
        </Text>
      </Box>
    </Group>
  );
}
