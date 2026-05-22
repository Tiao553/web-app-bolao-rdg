import { Avatar, Badge, Group, Table, Text } from '@mantine/core';

export type RankingRow = {
  userId: string;
  position: number;
  name: string;
  points: number;
  accessStatus?: string;
};

type LeaderboardTableProps = {
  rows: RankingRow[];
  currentUserId?: string;
};

const podiumStyle: Record<number, { bg: string; border: string; posColor: string }> = {
  1: { bg: 'rgba(234,179,8,0.08)',   border: 'rgba(234,179,8,0.2)',   posColor: 'var(--rdg-gold)' },
  2: { bg: 'rgba(148,163,184,0.06)', border: 'rgba(148,163,184,0.15)', posColor: 'var(--rdg-silver)' },
  3: { bg: 'rgba(180,83,9,0.08)',    border: 'rgba(180,83,9,0.2)',    posColor: 'var(--rdg-bronze)' },
};

function getInitials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((n) => n[0])
    .join('')
    .toUpperCase();
}

export function LeaderboardTable({ rows, currentUserId }: LeaderboardTableProps) {
  return (
    <Table
      striped={false}
      highlightOnHover={false}
      style={{ borderRadius: 'var(--mantine-radius-md)', overflow: 'hidden', border: '1px solid var(--rdg-bd)' }}
    >
      <Table.Thead>
        <Table.Tr style={{ background: 'var(--rdg-s2)' }}>
          <Table.Th style={{ width: 40 }}>
            <Text size="xs" c="dimmed" ff="monospace" style={{ letterSpacing: '0.1em' }}>#</Text>
          </Table.Th>
          <Table.Th>
            <Text size="xs" c="dimmed" ff="monospace" style={{ letterSpacing: '0.1em' }}>Participante</Text>
          </Table.Th>
          <Table.Th style={{ textAlign: 'right', width: 64 }}>
            <Text size="xs" c="dimmed" ff="monospace" style={{ letterSpacing: '0.1em' }}>Pts</Text>
          </Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {rows.map((row) => {
          const podium = podiumStyle[row.position];
          const isMe = row.userId === currentUserId;

          return (
            <Table.Tr
              key={row.userId}
              style={{
                background: podium?.bg ?? (isMe ? 'var(--rdg-or-g, rgba(249,115,22,0.06))' : 'transparent'),
                borderBottom: '1px solid var(--rdg-bd)',
                outline: isMe && !podium ? '1px solid var(--mantine-color-rdg-orange-5)' : undefined,
              }}
            >
              <Table.Td>
                <Text
                  ff="monospace"
                  size="sm"
                  fw={600}
                  style={{ color: podium?.posColor ?? (isMe ? 'var(--mantine-color-rdg-orange-5)' : 'var(--rdg-tx3)') }}
                >
                  {row.position}
                </Text>
              </Table.Td>
              <Table.Td>
                <Group gap="sm" wrap="nowrap">
                  <Avatar
                    size="sm"
                    radius="xl"
                    color="rdg-orange"
                    variant="light"
                  >
                    {getInitials(row.name)}
                  </Avatar>
                  <Text size="sm" fw={isMe ? 600 : 400} truncate="end" style={{ maxWidth: 200 }}>
                    {row.name}
                    {isMe && (
                      <Text component="span" size="xs" c="rdg-orange" ml={6} ff="monospace">
                        (você)
                      </Text>
                    )}
                  </Text>
                </Group>
              </Table.Td>
              <Table.Td style={{ textAlign: 'right' }}>
                <Text
                  ff="monospace"
                  fw={700}
                  size="sm"
                  c={podium ? undefined : isMe ? 'rdg-orange' : undefined}
                  style={{
                    color: podium?.posColor,
                  }}
                >
                  {row.points}
                </Text>
              </Table.Td>
            </Table.Tr>
          );
        })}
      </Table.Tbody>
    </Table>
  );
}
