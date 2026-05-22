import { redirect } from 'next/navigation';
import { Card, Grid, Group, Stack, Text, Title } from '@mantine/core';
import { BrandLogo } from '../../../components/brand/brand-logo';
import { fetchAppSession, resolveHomePath } from '../../../lib/session';

const copyByStatus = {
  PENDING: {
    title: 'Sua conta está em análise.',
    description: 'O cadastro foi recebido, mas ainda precisa ser aprovado para participar do bolão.'
  },
  REJECTED: {
    title: 'Seu cadastro não foi liberado.',
    description: 'Procure um administrador se quiser revisar os dados enviados.'
  },
  BLOCKED: {
    title: 'Sua conta está bloqueada.',
    description: 'O acesso ao bolão foi suspenso até nova revisão administrativa.'
  }
};

export default async function WaitingPage() {
  const session = await fetchAppSession();

  if (!session.authenticated || !session.user) {
    redirect('/login');
  }

  if (session.accessStatus === 'APPROVED') {
    redirect(resolveHomePath(session));
  }

  const status = session.accessStatus === 'REJECTED' || session.accessStatus === 'BLOCKED' ? session.accessStatus : 'PENDING';
  const copy = copyByStatus[status];

  return (
    <Grid mih="100vh" p="xl" gutter="xl">
      <Grid.Col span={{ base: 12, lg: 7 }}>
        <Card radius={34} p="xl" h="100%" style={{ minHeight: 'calc(100vh - 48px)', background: 'linear-gradient(145deg, rgba(255,255,255,.045), rgba(255,255,255,.015)), var(--rdg-s0)', border: '1px solid var(--rdg-bd)' }}>
          <Stack justify="space-between" h="100%">
            <BrandLogo size="lg" />
            <Stack gap="xl" maw={640}>
              <Text ff="monospace" c="rdg-orange.5" tt="uppercase" style={{ letterSpacing: '0.12em' }}>status do acesso</Text>
              <Title order={1} fz={{ base: 40, md: 72 }} lh={0.92}>A conta ainda não entrou em <Text component="span" inherit c="rdg-orange.5">campo</Text>.</Title>
              <Text size="lg" c="dimmed">Enquanto isso, o fluxo de aprovação garante governança, evita múltiplas contas e mantém o ranking restrito a participantes realmente liberados.</Text>
            </Stack>
            <Group grow>
              <Card radius={18} p="lg" style={{ border: '1px solid var(--rdg-bd2)', background: 'rgba(20,20,24,.72)' }}><Text fw={800}>Cadastro autenticado</Text><Text size="sm" c="dimmed">Sua sessão já está ativa.</Text></Card>
              <Card radius={18} p="lg" style={{ border: '1px solid var(--rdg-bd2)', background: 'rgba(20,20,24,.72)' }}><Text fw={800}>Revisão manual</Text><Text size="sm" c="dimmed">O admin decide a liberação final.</Text></Card>
              <Card radius={18} p="lg" style={{ border: '1px solid var(--rdg-bd2)', background: 'rgba(20,20,24,.72)' }}><Text fw={800}>Dashboard depois</Text><Text size="sm" c="dimmed">A rota correta será aberta automaticamente.</Text></Card>
            </Group>
          </Stack>
        </Card>
      </Grid.Col>
      <Grid.Col span={{ base: 12, lg: 5 }}>
        <Card radius={34} p="xl" h="100%" style={{ minHeight: 'calc(100vh - 48px)', background: 'rgba(255,255,255,.96)', color: '#18181B' }}>
          <Stack justify="center" h="100%" ta="center" maw={460} mx="auto">
            <BrandLogo />
            <Text ff="monospace" tt="uppercase" c="orange.6" style={{ letterSpacing: '0.12em' }}>{status}</Text>
            <Title order={2}>{copy.title}</Title>
            <Text c="dimmed">{copy.description}</Text>
            <Card radius="xl" p="lg" bg="gray.0">
              <Stack gap="xs">
                <Text fw={800}>Conta</Text>
                <Text>{session.user.name}</Text>
                <Text size="sm" c="dimmed">{session.user.email}</Text>
              </Stack>
            </Card>
          </Stack>
        </Card>
      </Grid.Col>
    </Grid>
  );
}
