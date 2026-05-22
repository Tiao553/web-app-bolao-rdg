'use client';

import { Box, Button, PasswordInput, Stack, Text, TextInput } from '@mantine/core';

const ERROR_MESSAGES: Record<string, string> = {
  email_already_registered: 'Esse e-mail já está cadastrado.',
  missing_name: 'Nome é obrigatório.',
  weak_password: 'A senha deve ter no mínimo 8 caracteres.',
  server_error: 'Erro no servidor. Tente novamente.',
  unknown: 'Algo deu errado. Tente novamente.',
};

type RegisterFormProps = {
  error?: string;
};

export function RegisterForm({ error }: RegisterFormProps) {
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

      <form action="/api/auth/register" method="post">
        <Stack gap="sm">
          <TextInput
            name="name"
            label="Nome"
            placeholder="Seu nome completo"
            required
            styles={{ input: { background: 'var(--rdg-s2)', borderColor: 'var(--rdg-bd)' } }}
          />
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
            placeholder="Mínimo 8 caracteres"
            required
            styles={{ input: { background: 'var(--rdg-s2)', borderColor: 'var(--rdg-bd)' } }}
          />
          <Button type="submit" color="rdg-orange" variant="outline" fullWidth mt="xs">
            Criar conta
          </Button>
        </Stack>
      </form>
    </Stack>
  );
}
