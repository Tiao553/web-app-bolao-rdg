import { Badge } from '@mantine/core';

type AccessStatus = 'APPROVED' | 'PENDING' | 'REJECTED' | 'BLOCKED';

type StatusBadgeProps = {
  status: AccessStatus | string | null | undefined;
};

const colorMap: Record<AccessStatus, string> = {
  APPROVED: 'green',
  PENDING: 'yellow',
  REJECTED: 'red',
  BLOCKED: 'gray',
};

const labelMap: Record<AccessStatus, string> = {
  APPROVED: 'Aprovado',
  PENDING: 'Pendente',
  REJECTED: 'Rejeitado',
  BLOCKED: 'Bloqueado',
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const key = (status ?? '') as AccessStatus;
  const color = colorMap[key] ?? 'gray';
  const label = labelMap[key] ?? (status ?? '—');

  return (
    <Badge color={color} variant="light" radius="xl" size="sm" ff="monospace">
      {label}
    </Badge>
  );
}
