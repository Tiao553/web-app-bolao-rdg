import type { ReactNode } from "react";
import { Alert, Stack, Text, Title } from '@mantine/core';

export type AccessStatus = "PENDING" | "APPROVED" | "REJECTED" | "BLOCKED";

export type AccessGateState =
  | "loading"
  | "error"
  | "pending"
  | "rejected"
  | "blocked"
  | "locked"
  | "allowed";

export type AccessGateProps = {
  accessStatus?: AccessStatus | null;
  approved?: boolean;
  released?: boolean;
  loading?: boolean;
  error?: string | null;
  children: ReactNode;
  loadingFallback?: ReactNode;
  pendingFallback?: ReactNode;
  rejectedFallback?: ReactNode;
  blockedFallback?: ReactNode;
  lockedFallback?: ReactNode;
  errorFallback?: ReactNode;
  fallback?: ReactNode;
};

function GateMessage({
  title,
  description
}: {
  title: string;
  description: string;
}) {
  return (
    <Alert radius="xl" color="orange" variant="light" aria-live="polite">
      <Stack gap={4}>
        <Title order={4}>{title}</Title>
        <Text c="dimmed">{description}</Text>
      </Stack>
    </Alert>
  );
}

function getGateState({
  accessStatus,
  approved,
  released,
  loading,
  error
}: Pick<
  AccessGateProps,
  "accessStatus" | "approved" | "released" | "loading" | "error"
>): AccessGateState {
  if (loading) {
    return "loading";
  }

  if (error) {
    return "error";
  }

  if (accessStatus === "PENDING") {
    return "pending";
  }

  if (accessStatus === "REJECTED") {
    return "rejected";
  }

  if (accessStatus === "BLOCKED") {
    return "blocked";
  }

  if (approved === false) {
    return "pending";
  }

  if (released === false) {
    return "locked";
  }

  return "allowed";
}

export function AccessGate(props: AccessGateProps) {
  const state = getGateState(props);

  if (state === "allowed") {
    return <>{props.children}</>;
  }

  if (state === "loading") {
    return (
      <>
        {props.loadingFallback ??
          props.fallback ?? (
            <GateMessage
              title="Carregando acesso"
              description="Estamos validando sua sessão e liberando a área correta."
            />
          )}
      </>
    );
  }

  if (state === "error") {
    return (
      <>
        {props.errorFallback ??
          props.fallback ?? (
            <GateMessage
              title="Não foi possível validar o acesso"
              description={props.error ?? "Tente novamente em instantes."}
            />
          )}
      </>
    );
  }

  if (state === "pending") {
    return (
      <>
        {props.pendingFallback ??
          props.fallback ?? (
            <GateMessage
              title="Aguardando aprovação"
              description="Sua conta está autenticada, mas ainda não foi liberada para participar do bolão."
            />
          )}
      </>
    );
  }

  if (state === "rejected") {
    return (
      <>
        {props.rejectedFallback ??
          props.fallback ?? (
            <GateMessage
              title="Acesso não liberado"
              description="Sua solicitação foi rejeitada. Procure um administrador para revisar o cadastro."
            />
          )}
      </>
    );
  }

  if (state === "blocked") {
    return (
      <>
        {props.blockedFallback ??
          props.fallback ?? (
            <GateMessage
              title="Acesso bloqueado"
              description="Sua conta está bloqueada no momento. Procure um administrador para mais detalhes."
            />
          )}
      </>
    );
  }

  return (
    <>
      {props.lockedFallback ??
        props.fallback ?? (
          <GateMessage
            title="Área bloqueada"
            description="Esta área ainda não foi liberada para visualização."
          />
        )}
    </>
  );
}
