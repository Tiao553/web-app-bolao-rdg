'use client';

import { Box, Button, PasswordInput, Stack, Text, TextInput } from '@mantine/core';

const ERROR_MESSAGES: Record<string, string> = {
  invalid_credentials: 'E-mail ou senha incorretos.',
  server_error: 'Erro no servidor. Tente novamente.',
  unknown: 'Algo deu errado. Tente novamente.',
};

type LoginFormProps = {
  error?: string;
};

export function LoginForm({ error }: LoginFormProps) {
  const errorMsg = error ? (ERROR_MESSAGES[error] ?? ERROR_MESSAGES.unknown) : null;

  return (
    <Stack gap="md">
      {errorMsg && (
        <Box
          style={{
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: 'var(--mantine-radius-sm)',
            padding: '10px 14px',
          }}
        >
          <Text size="sm" c="red">{errorMsg}</Text>
        </Box>
      )}

      <form action="/api/auth/login" method="post">
        <Stack gap="sm">
          <TextInput
            name="email"
            type="email"
            label="E-mail"
            placeholder="voce@email.com"
            required
            styles={{ input: { background: 'var(--rdg-s2)', borderColor: 'var(--rdg-bd)' } }}
          />
          <PasswordInput
            name="password"
            label="Senha"
            required
            styles={{ input: { background: 'var(--rdg-s2)', borderColor: 'var(--rdg-bd)' } }}
          />
          <Button type="submit" color="rdg-orange" fullWidth mt="xs">
            Entrar
          </Button>
        </Stack>
      </form>
    </Stack>
  );
}
