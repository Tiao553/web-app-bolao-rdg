import Link from 'next/link';
import { Anchor, Button, Card, Grid, Group, SegmentedControl, Stack, Text, TextInput, Title } from '@mantine/core';
import { BrandLogo } from '../../../components/brand/brand-logo';

const errorMap: Record<string, string> = {
  email_already_registered: 'Este email já foi cadastrado.',
  server_error: 'Não foi possível criar a conta agora.',
  unknown: 'Não foi possível concluir o cadastro.'
};

export default async function CreateAccountPage({ searchParams }: { searchParams?: Promise<Record<string, string | string[] | undefined>>; }) {
  const params = searchParams ? await searchParams : {};
  const errorCode = typeof params.error === 'string' ? params.error : undefined;

  return (
    <Grid mih="100vh" p="xl" gutter="xl">
      <Grid.Col span={{ base: 12, lg: 5 }}>
        <Card radius={34} p="xl" h="100%" style={{ minHeight: 'calc(100vh - 48px)', background: 'rgba(255,255,255,.96)', color: '#18181B' }}>
          <Stack justify="center" h="100%" maw={460} mx="auto">
            <BrandLogo />
            <Stack gap={4} ta="center">
              <Title order={2}>Criar conta</Title>
              <Text size="sm" c="dimmed">Todo cadastro entra em fila de aprovação antes de participar do bolão.</Text>
            </Stack>
            <SegmentedControl fullWidth data={[{ label: 'Participante', value: 'participant' }, { label: 'Admin', value: 'admin' }]} value="participant" readOnly />
            {errorCode ? <Card radius="lg" p="md" bg="red.0"><Text c="red.8">{errorMap[errorCode] ?? errorMap.unknown}</Text></Card> : null}
            <form action="/api/auth/register" method="POST">
              <Stack>
                <TextInput name="name" label="Nome completo" required placeholder="Seu nome" />
                <TextInput name="email" type="email" label="Email" required placeholder="seu@email.com" />
                <TextInput name="password" type="password" label="Senha" required placeholder="Mínimo de 8 caracteres" />
                <Button type="submit">Enviar cadastro</Button>
              </Stack>
            </form>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Já tem conta?</Text>
              <Anchor component={Link} href="/login">Voltar para login</Anchor>
            </Group>
          </Stack>
        </Card>
      </Grid.Col>
      <Grid.Col span={{ base: 12, lg: 7 }}>
        <Card radius={34} p="xl" h="100%" style={{ minHeight: 'calc(100vh - 48px)', background: 'linear-gradient(145deg, rgba(255,255,255,.045), rgba(255,255,255,.015)), var(--rdg-s0)', border: '1px solid var(--rdg-bd)' }}>
          <Stack justify="space-between" h="100%">
            <BrandLogo size="lg" />
            <Stack gap="xl" maw={620}>
              <Text ff="monospace" c="rdg-orange.5" tt="uppercase" style={{ letterSpacing: '0.12em' }}>cadastro com governança</Text>
              <Title order={1} fz={{ base: 40, md: 68 }} lh={0.92}>Seu acesso só vira jogo depois da <Text component="span" inherit c="rdg-orange.5">aprovação</Text>.</Title>
              <Text c="dimmed" size="lg">O admin revisa duplicidades, bloqueios e liberação manual. O layout já reflete esse fluxo completo antes da área de membro.</Text>
            </Stack>
            <Group grow>
              <Card radius={18} p="lg" style={{ border: '1px solid var(--rdg-bd2)', background: 'rgba(20,20,24,.72)' }}><Text fw={800}>1. Cadastro</Text><Text size="sm" c="dimmed">Conta criada e sessão iniciada.</Text></Card>
              <Card radius={18} p="lg" style={{ border: '1px solid var(--rdg-bd2)', background: 'rgba(20,20,24,.72)' }}><Text fw={800}>2. Revisão</Text><Text size="sm" c="dimmed">Admin aprova, rejeita ou bloqueia.</Text></Card>
              <Card radius={18} p="lg" style={{ border: '1px solid var(--rdg-bd2)', background: 'rgba(20,20,24,.72)' }}><Text fw={800}>3. Liberação</Text><Text size="sm" c="dimmed">Dashboard e palpites ficam ativos.</Text></Card>
            </Group>
          </Stack>
        </Card>
      </Grid.Col>
    </Grid>
  );
}
