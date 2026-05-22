import Link from 'next/link';
import { Anchor, Button, Card, Grid, Group, SimpleGrid, Stack, Text, TextInput, Title } from '@mantine/core';
import { BrandLogo } from '../../../components/brand/brand-logo';

const errorMap: Record<string, string> = {
  invalid_credentials: 'Email ou senha inválidos.',
  server_error: 'Não foi possível conectar ao backend.',
  unknown: 'Não foi possível concluir o login.'
};

export default async function LoginPage({ searchParams }: { searchParams?: Promise<Record<string, string | string[] | undefined>>; }) {
  const params = searchParams ? await searchParams : {};
  const errorCode = typeof params.error === 'string' ? params.error : undefined;

  return (
    <Grid mih="100vh" p="xl" gutter="xl">
      <Grid.Col span={{ base: 12, lg: 7 }}>
        <Card radius={34} p="xl" h="100%" style={{ minHeight: 'calc(100vh - 48px)', background: 'linear-gradient(145deg, rgba(255,255,255,.045), rgba(255,255,255,.015)), var(--rdg-s0)', border: '1px solid var(--rdg-bd)' }}>
          <Stack justify="space-between" h="100%">
            <BrandLogo size="lg" />
            <Stack gap="xl" maw={620}>
              <Text ff="monospace" c="rdg-orange.5" tt="uppercase" style={{ letterSpacing: '0.12em' }}>bolão da copa · acesso governado</Text>
              <Title order={1} fz={{ base: 40, md: 74 }} lh={0.92}>Entre no <Text component="span" inherit c="rdg-orange.5">painel oficial</Text>.</Title>
              <Text c="dimmed" size="lg">Acesse seus palpites, acompanhe resultados, ranking, chaveamento e Explore no layout completo do Bolão Copa RDG.</Text>
            </Stack>
            <SimpleGrid cols={{ base: 1, md: 3 }}>
              <Card radius={18} p="lg" style={{ border: '1px solid var(--rdg-bd2)', background: 'rgba(20,20,24,.72)' }}><Text fw={800}>Acesso aprovado</Text><Text size="sm" c="dimmed">Rotas protegidas por sessão.</Text></Card>
              <Card radius={18} p="lg" style={{ border: '1px solid var(--rdg-bd2)', background: 'rgba(20,20,24,.72)' }}><Text fw={800}>Palpites bloqueáveis</Text><Text size="sm" c="dimmed">A regra continua no backend.</Text></Card>
              <Card radius={18} p="lg" style={{ border: '1px solid var(--rdg-bd2)', background: 'rgba(20,20,24,.72)' }}><Text fw={800}>Explore liberado</Text><Text size="sm" c="dimmed">Somente após o fechamento oficial.</Text></Card>
            </SimpleGrid>
          </Stack>
        </Card>
      </Grid.Col>
      <Grid.Col span={{ base: 12, lg: 5 }}>
        <Card radius={34} p="xl" h="100%" style={{ minHeight: 'calc(100vh - 48px)', background: 'rgba(255,255,255,.96)', color: '#18181B' }}>
          <Stack justify="center" h="100%" maw={440} mx="auto">
            <BrandLogo />
            <Stack gap={4} ta="center" mb="md">
              <Title order={2}>Entrar</Title>
              <Text size="sm" c="dimmed">Use a conta já aprovada ou aguarde liberação do administrador.</Text>
            </Stack>
            {errorCode ? <Card radius="lg" p="md" bg="red.0"><Text c="red.8">{errorMap[errorCode] ?? errorMap.unknown}</Text></Card> : null}
            <form action="/api/auth/login" method="POST">
              <Stack>
                <TextInput name="email" type="email" label="Email" required placeholder="seu@email.com" />
                <TextInput name="password" type="password" label="Senha" required placeholder="••••••••" />
                <Button type="submit" size="md">Entrar</Button>
              </Stack>
            </form>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Ainda não tem conta?</Text>
              <Anchor component={Link} href="/create-account">Criar conta</Anchor>
            </Group>
          </Stack>
        </Card>
      </Grid.Col>
    </Grid>
  );
}
